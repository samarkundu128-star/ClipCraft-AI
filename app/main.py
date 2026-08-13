import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, TEMP_DIR
from ai.gemini_engine import GeminiEngine
from ai.whisper_engine import SpeechToText
from media.ffmpeg_core import FFmpegCore
from app.utils.file_manager import cleanup_files

logging.basicConfig(level=logging.INFO)

gemini = GeminiEngine()
whisper_stt = SpeechToText("base")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Welcome to AI Shorts Generator Bot!**\n\n"
        "📹 Mughe koi bhi long video (MP4/file) bhejo, main Gemini + FFmpeg use karke auto viral Shorts/Reels render kar doonga."
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📥 **Video download ho rahi hai...**")
    
    file = await update.message.video.get_file()
    input_video_path = os.path.join(TEMP_DIR, f"input_{update.message.message_id}.mp4")
    audio_path = os.path.join(TEMP_DIR, f"audio_{update.message.message_id}.mp3")
    output_short_path = os.path.join(TEMP_DIR, f"short_{update.message.message_id}.mp4")

    await file.download_to_drive(input_video_path)

    try:
        # Step 1: Extract Audio
        await msg.edit_text("🎧 **Audio extract and Speech-to-Text transcribe ho raha hai...**")
        FFmpegCore.extract_audio(input_video_path, audio_path)

        # Step 2: Whisper Transcription
        transcript_data = whisper_stt.transcribe(audio_path)

        # Step 3: Gemini Analysis
        await msg.edit_text("🧠 **Gemini AI best viral segment find kar raha hai...**")
        ai_result = gemini.analyze_content(transcript_data["text"])

        # Step 4: Render Clip via FFmpeg
        await msg.edit_text(f"✂️ **Rendering Shorts segment ({ai_result['start_time']} - {ai_result['end_time']})...**")
        FFmpegCore.trim_and_render_short(
            input_video_path,
            ai_result["start_time"],
            ai_result["end_time"],
            output_short_path
        )

        # Step 5: Send Back to Telegram
        await msg.edit_text("🚀 **Uploading final Short...**")
        caption_text = f"✨ **{ai_result['title']}**\n\n{ai_result['caption']}\n\n📊 *Viral Score:* {ai_result['viral_score']}/100"
        
        with open(output_short_path, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption=caption_text)

    except Exception as e:
        await update.message.reply_text(f"❌ Error aaya: {str(e)}")

    finally:
        # Step 6: Cleanup Temp files
        cleanup_files(input_video_path, audio_path, output_output_short_path if 'output_short_path' in locals() else None)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
  
