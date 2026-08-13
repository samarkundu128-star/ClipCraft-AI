import logging
import os
import threading
import asyncio
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Application Package Imports
from app.config import TELEGRAM_BOT_TOKEN, TEMP_DIR
from app.ai.gemini_engine import GeminiEngine
from app.ai.whisper_engine import SpeechToText
from app.media.ffmpeg_core import FFmpegCore
from app.utils.file_manager import cleanup_files

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 1. Fake HTTP Server for Render Free Tier Port Binding ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "ClipCraft AI Bot is Running Alive!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. Initialize AI Engines ---
gemini = GeminiEngine()
whisper_stt = SpeechToText("tiny")

# --- Helper Function: Link Se Video Download Karne Ke Liye ---
def _download_yt_video(url: str, output_path: str):
    """Blocking yt-dlp download function"""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def download_video_from_url(url: str, output_path: str):
    """Async wrapper so event loop isn't blocked"""
    await asyncio.to_thread(_download_yt_video, url, output_path)


# --- 3. Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handler"""
    await update.message.reply_text(
        "👋 **Welcome to AI Shorts Generator Bot!**\n\n"
        "📹 Mujhe koi bhi long video file ya **YouTube/Reels Link** bhejo, main Gemini + FFmpeg use karke auto viral Shorts render kar doonga.",
        parse_mode="Markdown"
    )


async def process_video_pipeline(msg, input_video_path: str, message_id: int, update: Update):
    """Core Processing Pipeline"""
    audio_path = os.path.join(TEMP_DIR, f"audio_{message_id}.mp3")
    output_short_path = os.path.join(TEMP_DIR, f"short_{message_id}.mp4")

    try:
        # Step 1: Extract Audio
        await msg.edit_text("🎧 **Audio extract ho raha hai...**", parse_mode="Markdown")
        FFmpegCore.extract_audio(input_video_path, audio_path)

        # Step 2: Whisper Speech-to-Text
        await msg.edit_text("🗣️ **Transcribe ho raha hai (Speech-to-Text)...**", parse_mode="Markdown")
        transcript_data = whisper_stt.transcribe(audio_path)

        # Step 3: Gemini Analysis
        await msg.edit_text("🧠 **Gemini AI best viral segment find kar raha hai...**", parse_mode="Markdown")
        ai_result = gemini.analyze_viral_moments(transcript_data["text"])

        # Step 4: Render Clip via FFmpeg
        await msg.edit_text(
            f"✂️ **Rendering Short segment ({ai_result['start_time']} - {ai_result['end_time']})...**",
            parse_mode="Markdown"
        )
        FFmpegCore.trim_and_render_short(
            input_video_path,
            ai_result["start_time"],
            ai_result["end_time"],
            output_short_path
        )

        # Step 5: Send Back to Telegram
        await msg.edit_text("🚀 **Uploading final Short...**", parse_mode="Markdown")
        caption_text = (
            f"✨ **{ai_result.get('title', 'Generated Short')}**\n\n"
            f"{ai_result.get('caption', '')}\n\n"
            f"📊 *Viral Score:* {ai_result.get('viral_score', 'N/A')}/100"
        )
        
        with open(output_short_path, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=caption_text,
                parse_mode="Markdown"
            )
            
        await msg.delete()

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        await msg.edit_text(f"❌ **Error aaya:** {str(e)}", parse_mode="Markdown")

    finally:
        cleanup_files(input_video_path, audio_path, output_short_path)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct Video Upload Handler"""
    msg = await update.message.reply_text("📥 **Video download ho rahi hai...**", parse_mode="Markdown")
    message_id = update.message.message_id
    input_video_path = os.path.join(TEMP_DIR, f"input_{message_id}.mp4")

    try:
        file = await update.message.video.get_file()
        await file.download_to_drive(input_video_path)
        await process_video_pipeline(msg, input_video_path, message_id, update)
    except Exception as e:
        logger.error(f"File Download Error: {e}")
        await msg.edit_text(f"❌ Video file download nahi ho paayi: {str(e)}")


async def handle_text_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """URL Link Handler"""
    text = update.message.text.strip()
    
    if "http://" in text or "https://" in text:
        msg = await update.message.reply_text("🔗 **Link detect hua! Video download ho rahi hai...**", parse_mode="Markdown")
        message_id = update.message.message_id
        input_video_path = os.path.join(TEMP_DIR, f"input_{message_id}.mp4")

        try:
            # Async way me call kar rahe hain taaki bot freeze na ho
            await download_video_from_url(text, input_video_path)
            
            if not os.path.exists(input_video_path):
                raise Exception("Downloaded file not found on disk.")

            await process_video_pipeline(msg, input_video_path, message_id, update)

        except Exception as e:
            logger.error(f"URL Download Error: {e}", exc_info=True)
            await msg.edit_text(f"❌ **Link se video download nahi ho paayi:**\n`{str(e)}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❓ Please valid Video File ya YouTube/Reels link bhejein.")


# --- 4. Main Function ---
def main():
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_url))
    
    print("🤖 Bot with Link Handler successfully started...")
    app.run_polling()


if __name__ == "__main__":
    main()
    
