import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class FFmpegCore:

    @staticmethod
    def extract_audio(input_video_path: str, output_audio_path: str):
        """
        Video se Audio extract karta hai (.wav format mein)
        """
        if not output_audio_path.endswith('.wav'):
            output_audio_path = os.path.splitext(output_audio_path)[0] + '.wav'

        command = [
            'ffmpeg',
            '-y',
            '-i', input_video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            output_audio_path
        ]
        
        logger.info(f"Running FFmpeg extract audio: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            if "does not contain any stream" in result.stderr or "Output file #0" in result.stderr:
                raise Exception("Is video file mein koi Audio / Sound track nahi hai! Please audio wali video bhejein.")
            raise Exception(f"FFmpeg Audio Extraction Failed:\n{result.stderr}")

    @staticmethod
    def trim_and_render_short(input_video_path: str, start_time: str, end_time: str, output_path: str):
        """
        Video clip ko specified timing par cut karke Short generate karta hai
        """
        command = [
            'ffmpeg',
            '-y',
            '-ss', str(start_time),
            '-to', str(end_time),
            '-i', input_video_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path
        ]
        
        logger.info(f"Running FFmpeg trim: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg render error: {result.stderr}")
            raise Exception(f"FFmpeg Trim Failed:\n{result.stderr}")
                              
