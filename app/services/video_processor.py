import os
from pathlib import Path
from app.media.ffmpeg_core import FFmpegCore
from app.media.models import RenderConfig, CropMode, QualityPreset
from app.services.file_manager import create_job_dir, cleanup_job_dir

ffmpeg_engine = FFmpegCore()

async def process_video_job(job_id: str, input_video_path: str) -> str:
    # 1. Job folder setup
    job_dir = create_job_dir(job_id)
    audio_path = str(job_dir / "whisper_input.wav")
    output_path = str(job_dir / "output_short.mp4")

    try:
        # 2. Extract Audio for Whisper AI
        await ffmpeg_engine.extract_whisper_audio(
            input_path=input_video_path,
            output_wav_path=audio_path
        )
        
        # 3. Whisper / AI Editing Decision Logic yahan run karein
        # (Transcribe -> Highlight selection -> Timestamps decision)

        # 4. Vertical 9:16 Short Render
        config = RenderConfig(
            target_width=1080,
            target_height=1920,
            quality=QualityPreset.HIGH,
            crop_mode=CropMode.BLUR_BACKGROUND
        )

        final_output = await ffmpeg_engine.render_shorts_vertical(
            input_path=input_video_path,
            output_path=output_path,
            config=config
        )

        return final_output

    except Exception as e:
        print(f"Job {job_id} failed: {str(e)}")
        raise e

    finally:
        # Note: Success ke baad file upload hone tak temp cleanup hold rakh sakte ho
        pass
        
