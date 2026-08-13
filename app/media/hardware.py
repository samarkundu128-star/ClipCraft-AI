"""Hardware encoder detection and fallback service."""

import logging
from typing import Optional
from app.media.subprocess_engine import AsyncSubprocessEngine

logger = logging.getLogger(__name__)


class HardwareAccelerationDetector:
    _cached_encoder: Optional[str] = None

    @classmethod
    async def get_best_h264_encoder(cls, ffmpeg_bin: str = "ffmpeg") -> str:
        """Detects available hardware-accelerated H.264 encoders or defaults to libx264."""
        if cls._cached_encoder:
            return cls._cached_encoder

        candidates = [
            ("h264_nvenc", ["-f", "lavfi", "-i", "nullsrc", "-c:v", "h264_nvenc", "-frames:v", "1", "-f", "null", "-"]),
            ("h264_qsv", ["-f", "lavfi", "-i", "nullsrc", "-c:v", "h264_qsv", "-frames:v", "1", "-f", "null", "-"]),
            ("h264_videotoolbox", ["-f", "lavfi", "-i", "nullsrc", "-c:v", "h264_videotoolbox", "-frames:v", "1", "-f", "null", "-"]),
            ("h264_vaapi", ["-f", "lavfi", "-i", "nullsrc", "-c:v", "h264_vaapi", "-frames:v", "1", "-f", "null", "-"]),
        ]

        for encoder_name, test_cmd in candidates:
            try:
                cmd = [ffmpeg_bin] + test_cmd
                await AsyncSubprocessEngine.run_command(cmd, timeout=5.0)
                logger.info("Hardware acceleration detected: using %s", encoder_name)
                cls._cached_encoder = encoder_name
                return encoder_name
            except Exception:
                continue

        logger.info("No supported hardware acceleration found. Falling back to libx264 software encoder.")
        cls._cached_encoder = "libx264"
        return "libx264"
      
