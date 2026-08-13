"""Production-grade local media processing engine."""

import os
import shutil
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from app.media.models import MediaMetadata, TrimRange, RenderConfig
from app.media.exceptions import (
    FFmpegNotFoundError, FFprobeNotFoundError, InvalidMediaError,
    NoAudioStreamError, NoVideoStreamError, RenderValidationError,
    InsufficientDiskSpaceError
)
from app.media.probe import MediaProbeService
from app.media.subprocess_engine import AsyncSubprocessEngine
from app.media.hardware import HardwareAccelerationDetector
from app.media.command_builder import CommandBuilder

logger = logging.getLogger(__name__)


class FFmpegCore:
    def __init__(
        self,
        ffmpeg_bin: str = "ffmpeg",
        ffprobe_bin: str = "ffprobe",
        min_disk_margin_mb: int = 500
    ):
        self.ffmpeg_bin = shutil.which(ffmpeg_bin) or ffmpeg_bin
        self.ffprobe_bin = shutil.which(ffprobe_bin) or ffprobe_bin
        self.min_disk_margin_mb = min_disk_margin_mb
        self.probe_service = MediaProbeService(ffprobe_binary=self.ffprobe_bin)
        self._verify_executables()

    def _verify_executables(self):
        if not shutil.which(self.ffmpeg_bin) and not os.path.exists(self.ffmpeg_bin):
            raise FFmpegNotFoundError(f"FFmpeg binary not available at: {self.ffmpeg_bin}")
        if not shutil.which(self.ffprobe_bin) and not os.path.exists(self.ffprobe_bin):
            raise FFprobeNotFoundError(f"FFprobe binary not available at: {self.ffprobe_bin}")

    def _check_disk_space(self, target_dir: str, required_bytes: int = 0):
        stat = shutil.disk_usage(target_dir)
        free_mb = stat.free / (1024 * 1024)
        required_mb = (required_bytes / (1024 * 1024)) + self.min_disk_margin_mb
        if free_mb < required_mb:
            raise InsufficientDiskSpaceError(
                f"Insufficient disk space in {target_dir}. Free: {free_mb:.1f}MB, Required: {required_mb:.1f}MB"
            )

    async def extract_whisper_audio(
        self,
        input_path: str,
        output_wav_path: str,
        timeout: float = 300.0,
        cancellation_event: Optional[asyncio.Event] = None
    ) -> str:
        """Extracts mono 16kHz PCM WAV audio specifically formatted for Whisper speech recognition."""
        metadata = await self.probe_service.probe(input_path)
        if not metadata.has_audio:
            raise NoAudioStreamError(f"Input video contains no audio stream: {input_path}")

        out_dir = os.path.dirname(output_wav_path) or "."
        self._check_disk_space(out_dir)

        partial_output = f"{output_wav_path}.partial.wav"

        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", input_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            partial_output
        ]

        try:
            await AsyncSubprocessEngine.run_command(cmd, timeout=timeout, cancellation_event=cancellation_event)
            
            # Validation
            if not os.path.exists(partial_output) or os.path.getsize(partial_output) == 0:
                raise RenderValidationError("Extracted audio output file is empty.")
            
            os.replace(partial_output, output_wav_path)
            return output_wav_path

        finally:
            if os.path.exists(partial_output):
                os.remove(partial_output)

    async def trim_video(
        self,
        input_path: str,
        output_path: str,
        trim_range: TrimRange,
        accurate: bool = True,
        timeout: float = 300.0,
        cancellation_event: Optional[asyncio.Event] = None
    ) -> str:
        """Trims video segment with fast stream-copy or frame-accurate re-encoding."""
        metadata = await self.probe_service.probe(input_path)
        if trim_range.end_seconds > metadata.duration + 0.5:
            raise InvalidMediaError(f"Trim end time {trim_range.end_seconds}s exceeds video duration {metadata.duration}s")

        out_dir = os.path.dirname(output_path) or "."
        self._check_disk_space(out_dir, required_bytes=metadata.size_bytes)

        partial_output = f"{output_path}.partial.mp4"

        if accurate:
            cmd = [
                self.ffmpeg_bin, "-y",
                "-ss", str(trim_range.start_seconds),
                "-to", str(trim_range.end_seconds),
                "-i", input_path,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                partial_output
            ]
        else:
            cmd = [
                self.ffmpeg_bin, "-y",
                "-ss", str(trim_range.start_seconds),
                "-to", str(trim_range.end_seconds),
                "-i", input_path,
                "-c", "copy",
                partial_output
            ]

        try:
            await AsyncSubprocessEngine.run_command(cmd, timeout=timeout, cancellation_event=cancellation_event)
            
            # Post-render Output Validation
            out_meta = await self.probe_service.probe(partial_output, use_cache=False)
            if out_meta.duration <= 0 or os.path.getsize(partial_output) == 0:
                raise RenderValidationError("Trimmed video output failed validation.")

            os.replace(partial_output, output_path)
            return output_path

        finally:
            if os.path.exists(partial_output):
                os.remove(partial_output)

    async def render_shorts_vertical(
        self,
        input_path: str,
        output_path: str,
        config: RenderConfig,
        timeout: float = 600.0,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancellation_event: Optional[asyncio.Event] = None
    ) -> str:
        """Renders input video to 9:16 vertical Short format with hardware acceleration fallback."""
        metadata = await self.probe_service.probe(input_path)
        if not metadata.has_video:
            raise NoVideoStreamError(f"Input file lacks a video stream: {input_path}")

        out_dir = os.path.dirname(output_path) or "."
        self._check_disk_space(out_dir, required_bytes=metadata.size_bytes * 2)

        partial_output = f"{output_path}.partial.mp4"

        encoder = "libx264"
        if config.hardware_accel:
            encoder = await HardwareAccelerationDetector.get_best_h264_encoder(self.ffmpeg_bin)

        cmd = CommandBuilder.build_shorts_render_cmd(
            self.ffmpeg_bin,
            input_path,
            partial_output,
            encoder,
            config,
            has_audio=metadata.has_audio
        )

        try:
            await AsyncSubprocessEngine.run_command(
                cmd,
                timeout=timeout,
                on_progress=on_progress,
                cancellation_event=cancellation_event
            )

            # Output validation
            out_meta = await self.probe_service.probe(partial_output, use_cache=False)
            if not out_meta.has_video or out_meta.size_bytes == 0:
                raise RenderValidationError("Rendered 9:16 Short failed validation.")

            os.replace(partial_output, output_path)
            return output_path

        except Exception as e:
            # Fallback to software encoder if hardware encoder fails during render
            if encoder != "libx264":
                logger.warning("Hardware render failed. Retrying render with software libx264 encoder: %s", str(e))
                cmd = CommandBuilder.build_shorts_render_cmd(
                    self.ffmpeg_bin, input_path, partial_output, "libx264", config, metadata.has_audio
                )
                await AsyncSubprocessEngine.run_command(cmd, timeout=timeout, cancellation_event=cancellation_event)
                os.replace(partial_output, output_path)
                return output_path
            raise

        finally:
            if os.path.exists(partial_output):
                os.remove(partial_output)
        
