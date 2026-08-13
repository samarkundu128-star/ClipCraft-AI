import subprocess
from app.utils.logger import logger

class FFmpegCore:
    @staticmethod
    def extract_audio(input_path: str, output_audio: str):
        # SECURE: List arguments prevent shell command injection
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            output_audio
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def render_short_vertical(input_path: str, start_time: str, end_time: str, output_path: str):
        # SECURE & OPTIMIZED: 1080x1920 crop/pad with Ultrafast x264 encoder
        cmd = [
            "ffmpeg", "-y",
            "-ss", start_time,
            "-to", end_time,
            "-i", input_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      
