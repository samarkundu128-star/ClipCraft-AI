import os
import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Media engine imports
from app.media.ffmpeg_core import FFmpegCore
from app.media.models import RenderConfig, CropMode, QualityPreset

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FFmpeg Core Engine Instance
ffmpeg_engine = FFmpegCore()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    await update.message.reply_text(
        "👋 Hi! Main aapka AI Video Editor Bot hoon.\n"
        "Mujhe koi video bhejo, main use Shorts/Reels (9:16 format) me convert kar dunga!"
    )


async def process_video_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video download, processing, and output pipeline."""
    message = update.message
    video = message.video or message.document

    if not video:
        await message.reply_text("Kripya ek valid video file bhejein.")
        return

    status_msg = await message.reply_text("📥 Video download ho rahi hai...")
    
    # Unique Job ID setup
    job_id = f"job_{message.chat_id}_{message.message_id}"
    job_dir = Path(f"temp/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)

    input_video_path = str(job_dir / "input_video.mp4")
    audio_path = str(job_dir / "whisper_input.wav")
    output_video_path = str(job_dir / "output_short.mp4")

    try:
        # 1. Download Video from Telegram
        file = await context.bot.get_file(video.file_id)
        await file.download_to_drive(input_video_path)

        # 2. Extract Audio for AI / Whisper
        await status_msg.edit_text("🎵 Audio extract ki ja rahi hai...")
        await ffmpeg_engine.extract_whisper_audio(
            input_path=input_video_path,
            output_wav_path=audio_path
        )

        # 3. Render 9:16 Vertical Video (FFmpeg Processing)
        await status_msg.edit_text("🎬 Video process & render ho rahi hai (9:16)...")
        render_config = RenderConfig(
            target_width=1080,
            target_height=1920,
            quality=QualityPreset.HIGH,
            crop_mode=CropMode.BLUR_BACKGROUND
        )

        await ffmpeg_engine.render_shorts_vertical(
            input_path=input_video_path,
            output_path=output_video_path,
            config=render_config
        )

        # 4. Upload Final Processed Video back to User
        await status_msg.edit_text("📤 Final video upload ho rahi hai...")
        with open(output_video_path, "rb") as video_file:
            await message.reply_video(
                video=video_file,
                caption="✅ Aapka Short/Reel ready hai!"
            )
        
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Pipeline processing error: {str(e)}", exc_info=True)
        await status_msg.edit_text(f"❌ Video process karne me error aaya: {str(e)}")

    finally:
        # Cleanup temporary files
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir, ignore_errors=True)


def main():
    """Bot initialization and startup."""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable set nahi hai!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, process_video_pipeline))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
        
