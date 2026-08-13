"""Type-safe models and data structures for media operations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class QualityPreset(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH = "high"
    MAX_QUALITY = "max_quality"


class CropMode(str, Enum):
    CROP = "crop"
    FIT = "fit"
    SMART_CROP = "smart_crop"
    BLUR_BACKGROUND = "blur_background"


class SubtitleStyle(str, Enum):
    DEFAULT = "default"
    BOTTOM_CENTER = "bottom_center"
    BOXED = "boxed"


@dataclass(frozen=True)
class StreamInfo:
    index: int
    codec_type: str  # "video" or "audio"
    codec_name: str
    bitrate: Optional[int] = None
    # Video-specific fields
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    pixel_format: Optional[str] = None
    sar: Optional[str] = None
    dar: Optional[str] = None
    rotation: int = 0
    # Audio-specific fields
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


@dataclass(frozen=True)
class MediaMetadata:
    file_path: str
    format_name: str
    duration: float
    size_bytes: int
    bitrate: int
    streams: list[StreamInfo] = field(default_factory=list)
    has_video: bool = False
    has_audio: bool = False
    
    @property
    def primary_video_stream(self) -> Optional[StreamInfo]:
        for s in self.streams:
            if s.codec_type == "video":
                return s
        return None

    @property
    def primary_audio_stream(self) -> Optional[StreamInfo]:
        for s in self.streams:
            if s.codec_type == "audio":
                return s
        return None


@dataclass
class TrimRange:
    start_seconds: float
    end_seconds: float

    def __post_init__(self):
        if self.start_seconds < 0:
            raise ValueError("Start time cannot be negative.")
        if self.end_seconds <= self.start_seconds:
            raise ValueError("End time must be strictly greater than start time.")

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass
class AudioMixConfig:
    voice_volume: float = 1.0
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.2
    enable_ducking: bool = True
    ducking_threshold: float = -20.0
    fade_in_duration: float = 0.5
    fade_out_duration: float = 0.5


@dataclass
class RenderConfig:
    target_width: int = 1080
    target_height: int = 1920
    fps: int = 30
    quality: QualityPreset = QualityPreset.HIGH
    crop_mode: CropMode = CropMode.BLUR_BACKGROUND
    hardware_accel: bool = True
    subtitle_path: Optional[str] = None
    audio_mix: Optional[AudioMixConfig] = None
    smart_crop_x_offset: Optional[float] = None  # Normalized [0.0, 1.0] center offset
  
