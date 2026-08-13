from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to AI Video Automation Bot!**\n\n"
        "Mughe koi bhi MP4 video bhejhein ya link share karein.\n"
        "Main Gemini AI aur FFmpeg se best viral short create kar doonga."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
  
