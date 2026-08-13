import subprocess
import os

class FFmpegCore:
    @staticmethod
    def extract_audio(input_path: str, output_audio: str):
        cmd = f"ffmpeg -y -i \"{input_path}\" -vn -acodec libmp3lame -q:a 2 \"{output_audio}\""
        subprocess.run(cmd, shell=True, check=True)

    @staticmethod
    def trim_and_render_short(input_path: str, start_time: str, end_time: str, output_path: str):
        # Cuts clip and converts standard 16:9 to 9:16 vertical shorts format with padding/crop
        cmd = (
            f"ffmpeg -y -ss {start_time} -to {end_time} -i \"{input_path}\" "
            f"-vf \"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2\" "
            f"-c:v libx264 -crf 18 -preset fast -c:a aac \"{output_path}\""
        )
        subprocess.run(cmd, shell=True, check=True)
      
