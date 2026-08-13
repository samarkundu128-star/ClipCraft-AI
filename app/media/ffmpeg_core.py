import subprocess
import logging

logger = logging.getLogger(__name__)

class FFmpegCore:
    @staticmethod
    def extract_audio(input_video: str, output_audio: str):
        """Video se 16kHz Mono WAV Audio Extract karta hai"""
        logger.info(f"Running FFmpeg extract audio: ffmpeg -y -i {input_video} -vn -acodec pcm_s16le -ar 16000 -ac 1 {output_audio}")
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_audio
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg audio extraction error: {result.stderr}")

    @staticmethod
    def trim_and_render_short(input_video: str, start_time: str, end_time: str, output_video: str):
        """Video ko fast trim karta hai without re-encoding lag"""
        logger.info(f"Trimming video from {start_time} to {end_time}")
        cmd = [
            "ffmpeg", "-y",
            "-ss", start_time,
            "-to", end_time,
            "-i", input_video,
            "-c", "copy",
            output_video
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg trim error: {result.stderr}")
                
