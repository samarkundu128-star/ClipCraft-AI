"""Constructs FFmpeg complex filtergraphs and command-line execution sequences."""

from typing import List, Optional
from app.media.models import RenderConfig, CropMode, QualityPreset


class CommandBuilder:
    @staticmethod
    def build_shorts_render_cmd(
        ffmpeg_bin: str,
        input_path: str,
        output_path: str,
        encoder: str,
        config: RenderConfig,
        has_audio: bool
    ) -> List[str]:
        cmd = [ffmpeg_bin, "-y", "-progress", "pipe:1", "-i", input_path]

        filtergraph = CommandBuilder._build_video_filtergraph(config)
        cmd.extend(["-vf", filtergraph])

        # Encoder options based on preset
        cmd.extend(["-c:v", encoder])
        if encoder == "libx264":
            preset_map = {
                QualityPreset.FAST: "ultrafast",
                QualityPreset.BALANCED: "medium",
                QualityPreset.HIGH: "slow",
                QualityPreset.MAX_QUALITY: "veryslow",
            }
            cmd.extend(["-preset", preset_map.get(config.quality, "medium"), "-crf", "18"])

        cmd.extend(["-r", str(config.fps), "-pix_fmt", "yuv420p"])

        # Audio configuration
        if has_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.append("-an")

        cmd.extend(["-movflags", "+faststart", output_path])
        return cmd

    @staticmethod
    def _build_video_filtergraph(config: RenderConfig) -> str:
        tw, th = config.target_width, config.target_height

        if config.crop_mode == CropMode.CROP:
            return f"scale=w={tw}:h={th}:force_original_aspect_ratio=increase,crop={tw}:{th}"
        
        elif config.crop_mode == CropMode.FIT:
            return f"scale=w={tw}:h={th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"
        
        elif config.crop_mode == CropMode.BLUR_BACKGROUND:
            return (
                f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th},boxblur=20:10[bg];"
                f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )

        elif config.crop_mode == CropMode.SMART_CROP and config.smart_crop_x_offset is not None:
            # Use normalized offset to adjust crop position horizontally
            return f"scale=w=-1:h={th},crop=w={tw}:h={th}:x='(in_w-{tw})*{config.smart_crop_x_offset}':y=0"

        # Fallback to crop
        return f"scale=w={tw}:h={th}:force_original_aspect_ratio=increase,crop={tw}:{th}"
      
