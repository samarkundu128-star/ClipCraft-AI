"""FFprobe metadata extraction layer with caching support."""

import json
import os
from typing import Dict, Optional
from app.media.models import MediaMetadata, StreamInfo
from app.media.exceptions import FFprobeNotFoundError, MediaProbeError, InvalidMediaError
from app.media.subprocess_engine import AsyncSubprocessEngine


class MediaProbeService:
    def __init__(self, ffprobe_binary: str = "ffprobe"):
        self.ffprobe_binary = ffprobe_binary
        self._cache: Dict[str, MediaMetadata] = {}

    async def probe(self, file_path: str, use_cache: bool = True) -> MediaMetadata:
        """Inspects media file and extracts metadata using ffprobe."""
        if not os.path.exists(file_path):
            raise InvalidMediaError(f"Media file does not exist: {file_path}")
        
        abs_path = os.path.abspath(file_path)
        if use_cache and abs_path in self._cache:
            return self._cache[abs_path]

        cmd = [
            self.ffprobe_binary,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            abs_path
        ]

        try:
            stdout = await AsyncSubprocessEngine.run_command(cmd, timeout=15.0)
            data = json.loads(stdout)
        except Exception as e:
            raise MediaProbeError(f"Failed to probe file {file_path}: {str(e)}") from e

        streams = []
        has_video = False
        has_audio = False

        for stream_data in data.get("streams", []):
            codec_type = stream_data.get("codec_type")
            
            # Rotation parsing
            rotation = 0
            side_data_list = stream_data.get("side_data_list", [])
            for sd in side_data_list:
                if "rotation" in sd:
                    rotation = int(sd["rotation"])
            
            tags = stream_data.get("tags", {})
            if "rotate" in tags:
                rotation = int(tags["rotate"])

            info = StreamInfo(
                index=int(stream_data.get("index", 0)),
                codec_type=codec_type,
                codec_name=stream_data.get("codec_name", "unknown"),
                bitrate=int(stream_data.get("bit_rate")) if stream_data.get("bit_rate") else None,
                width=int(stream_data.get("width")) if stream_data.get("width") else None,
                height=int(stream_data.get("height")) if stream_data.get("height") else None,
                fps=self._parse_fps(stream_data.get("r_frame_rate")),
                pixel_format=stream_data.get("pix_fmt"),
                sar=stream_data.get("sample_aspect_ratio"),
                dar=stream_data.get("display_aspect_ratio"),
                rotation=rotation,
                sample_rate=int(stream_data.get("sample_rate")) if stream_data.get("sample_rate") else None,
                channels=int(stream_data.get("channels")) if stream_data.get("channels") else None,
            )
            
            if codec_type == "video":
                has_video = True
            elif codec_type == "audio":
                has_audio = True

            streams.append(info)

        format_info = data.get("format", {})
        metadata = MediaMetadata(
            file_path=abs_path,
            format_name=format_info.get("format_name", "unknown"),
            duration=float(format_info.get("duration", 0.0)),
            size_bytes=int(format_info.get("size", os.path.getsize(abs_path))),
            bitrate=int(format_info.get("bit_rate", 0)),
            streams=streams,
            has_video=has_video,
            has_audio=has_audio
        )

        if use_cache:
            self._cache[abs_path] = metadata

        return metadata

    @staticmethod
    def _parse_fps(fps_str: Optional[str]) -> Optional[float]:
        if not fps_str or fps_str == "0/0":
            return None
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/")
                return float(num) / float(den) if float(den) != 0 else None
            return float(fps_str)
        except ValueError:
            return None
          
