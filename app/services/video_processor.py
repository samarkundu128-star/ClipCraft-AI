# Before (Legacy Blocking Call)
# ffmpeg_core.trim_video(input_p, output_p, start, end)

# After (Async & Type-Safe)
from app.media.ffmpeg_core import FFmpegCore
from app.media.models import TrimRange, RenderConfig, CropMode, QualityPreset

ffmpeg_engine = FFmpegCore()

async def process_user_video(job_id: str, input_file: str, output_file: str):
    # 1. Extract Whisper Audio
    audio_path = f"temp/{job_id}/audio.wav"
    await ffmpeg_engine.extract_whisper_audio(input_file, audio_path)

    # 2. Render Vertical 9:16 Short
    config = RenderConfig(
        target_width=1080,
        target_height=1920,
        quality=QualityPreset.HIGH,
        crop_mode=CropMode.BLUR_BACKGROUND
    )
    
    await ffmpeg_engine.render_shorts_vertical(
        input_path=input_file,
        output_path=output_file,
        config=config
    )
  
