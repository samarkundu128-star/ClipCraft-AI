"""Domain-specific exception hierarchy for media processing."""

class FFmpegEngineError(Exception):
    """Base exception for all media engine errors."""
    pass


class FFmpegNotFoundError(FFmpegEngineError):
    """Raised when FFmpeg or FFprobe binaries are missing from the system path."""
    pass


class FFprobeNotFoundError(FFmpegEngineError):
    """Raised when FFprobe binary is missing from the system path."""
    pass


class MediaProbeError(FFmpegEngineError):
    """Raised when metadata probing fails on an input file."""
    pass


class InvalidMediaError(FFmpegEngineError):
    """Raised when an input file is corrupted, unreadable, or missing required streams."""
    pass


class NoVideoStreamError(InvalidMediaError):
    """Raised when an operation requires a video stream but none is found."""
    pass


class NoAudioStreamError(InvalidMediaError):
    """Raised when an operation requires an audio stream but none is found."""
    pass


class FFmpegTimeoutError(FFmpegEngineError):
    """Raised when an FFmpeg process execution exceeds its configured timeout limit."""
    pass


class FFmpegProcessError(FFmpegEngineError):
    """Raised when FFmpeg exits with a non-zero return code."""
    def __init__(self, message: str, return_code: int, stderr: str):
        super().__init__(message)
        self.return_code = return_code
        self.stderr = stderr


class RenderValidationError(FFmpegEngineError):
    """Raised when an output media file fails post-render validation checks."""
    pass


class InsufficientDiskSpaceError(FFmpegEngineError):
    """Raised when available disk space is below required operating thresholds."""
    pass


class JobCancelledError(FFmpegEngineError):
    """Raised when a processing job is explicitly cancelled by the client or queue."""
    pass
  
