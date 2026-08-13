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
logger.info("Initializing AI Engines...")
gemini = GeminiEngine()
whisper_stt = SpeechToText("tiny")


# --- Helper Function: Non-blocking Link Downloader ---
def _download_yt_video(url: str, output_path: str):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def download_video_from_url(url: str, output_path: str):
    await asyncio.to_thread(_download_yt_video, url, output_path)


# --- 3. Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handler"""
    await update.message.reply_text(
        "👋 **Welcome to AI Shorts Generator Bot!**\n\n"
        "📹 Mujhe koi bhi long video MP4 file ya **YouTube Link** bhejo.\n"
        "⚡ Aap ek saath multiple videos bhi bhej sakte hain!",
        parse_mode="Markdown"
    )


async def process_video_pipeline(msg, input_video_path: str, message_id: int, update: Update):
    """Detailed Pipeline with Clear Error Reporting"""
    audio_path = os.path.join(TEMP_DIR, f"audio_{message_id}.mp3")
    output_short_path = os.path.join(TEMP_DIR, f"short_{message_id}.mp4")

    try:
        # Step 1: FFmpeg Audio Extraction
        await msg.edit_text("🎧 **Step 1/5:** Video se Audio extract ho raha hai...", parse_mode="Markdown")
        try:
            FFmpegCore.extract_audio(input_video_path, audio_path)
        except Exception as e:
            raise Exception(f"Audio Extraction Failed: {str(e)}")

        # Step 2: Whisper Speech-to-Text
        await msg.edit_text("🗣️ **Step 2/5:** Whisper AI Speech-to-Text Transcribe kar raha hai...", parse_mode="Markdown")
        try:
            # Running transcription non-blocking
            transcript_data = await asyncio.to_thread(whisper_stt.transcribe, audio_path)
            
            if not transcript_data or not transcript_data.get("text"):
                raise Exception("Transcript text empty mila (Video me voice nahi mili ya Whisper fail ho gaya).")
        except Exception as e:
            raise Exception(f"Speech-to-Text Error: {str(e)}")

        # Step 3: Gemini Analysis
        await msg.edit_text("🧠 **Step 3/5:** Gemini AI viral segment identify kar raha hai...", parse_mode="Markdown")
        try:
            ai_result = await asyncio.to_thread(gemini.analyze_viral_moments, transcript_data["text"])
        except Exception as e:
            raise Exception(f"Gemini AI Analysis Error: {str(e)}")

        # Step 4: Render Clip via FFmpeg
        start_t = ai_result.get('start_time', '00:00:00')
        end_t = ai_result.get('end_time', '00:00:30')
        
        await msg.edit_text(
            f"✂️ **Step 4/5:** Short render ho raha hai...\n⏱️ Timing: `{start_t}` -> `{end_t}`",
            parse_mode="Markdown"
        )
        try:
            FFmpegCore.trim_and_render_short(input_video_path, start_t, end_t, output_short_path)
        except Exception as e:
            raise Exception(f"FFmpeg Clip Render Error: {str(e)}")

        # Step 5: Send Back to Telegram
        await msg.edit_text("🚀 **Step 5/5:** Final Short upload ho raha hai...", parse_mode="Markdown")
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
        logger.error(f"Pipeline processing error: {e}", exc_info=True)
        await msg.edit_text(
            f"❌ **Processing me error aaya:**\n\n`{str(e)}`", 
            parse_mode="Markdown"
        )

    finally:
        cleanup_files(input_video_path, audio_path, output_short_path)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct Video Upload Handler (Background Async Task)"""
    msg = await update.message.reply_text("📥 **Video file receive hui, download start ho rahi hai...**", parse_mode="Markdown")
    message_id = update.message.message_id
    input_video_path = os.path.join(TEMP_DIR, f"input_{message_id}.mp4")

    async def run_task():
        try:
            file = await update.message.video.get_file()
            await file.download_to_drive(input_video_path)
            await process_video_pipeline(msg, input_video_path, message_id, update)
        except Exception as e:
            logger.error(f"File Download Error: {e}")
            await msg.edit_text(f"❌ Video file download nahi ho paayi: `{str(e)}`", parse_mode="Markdown")

    # Run as independent task so next messages are not blocked
    asyncio.create_task(run_task())


async def handle_text_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """URL Link Handler (Background Async Task)"""
    text = update.message.text.strip()
    
    if "http://" in text or "https://" in text:
        msg = await update.message.reply_text("🔗 **Link receive hua! Video download start ho rahi hai...**", parse_mode="Markdown")
        message_id = update.message.message_id
        input_video_path = os.path.join(TEMP_DIR, f"input_{message_id}.mp4")

        async def run_task():
            try:
                await download_video_from_url(text, input_video_path)
                
                if not os.path.exists(input_video_path):
                    raise Exception("Video download complete nahi hui (File missing).")

                await process_video_pipeline(msg, input_video_path, message_id, update)

            except Exception as e:
                logger.error(f"URL Download Error: {e}", exc_info=True)
                await msg.edit_text(f"❌ **Link download error:**\n`{str(e)}`", parse_mode="Markdown")

        # Run as independent task for multi-video handling
        asyncio.create_task(run_task())
    else:
        await update.message.reply_text("❓ Please valid Video File ya YouTube link bhejein.")


# --- 4. Main Function ---
def main():
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_url))
    
    print("🤖 Bot with Detailed Logs & Async Task Support started...")
    app.run_polling()


if __name__ == "__main__":
    main()
