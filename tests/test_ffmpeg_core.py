import os
import pytest
import asyncio
from app.media.ffmpeg_core import FFmpegCore
from app.media.models import TrimRange, RenderConfig, CropMode
from app.media.exceptions import InvalidMediaError, NoAudioStreamError

@pytest.fixture
def ffmpeg_engine():
    return FFmpegCore()

@pytest.fixture
def sample_video(tmp_path):
    path = os.path.join(tmp_path, "test.mp4")
    # Generate 5-second test video with sine wave audio using lavfi
    cmd = f"ffmpeg -y -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 -f lavfi -i sine=frequency=1000:duration=5 {path}"
    os.system(cmd)
    return path

@pytest.mark.asyncio
async def test_media_probe(ffmpeg_engine, sample_video):
    metadata = await ffmpeg_engine.probe_service.probe(sample_video)
    assert metadata.has_video is True
    assert metadata.has_audio is True
    assert metadata.duration >= 4.9

@pytest.mark.asyncio
async def test_whisper_audio_extraction(ffmpeg_engine, sample_video, tmp_path):
    out_wav = os.path.join(tmp_path, "whisper.wav")
    await ffmpeg_engine.extract_whisper_audio(sample_video, out_wav)
    assert os.path.exists(out_wav)
    assert os.path.getsize(out_wav) > 0

@pytest.mark.asyncio
async def test_shorts_vertical_render(ffmpeg_engine, sample_video, tmp_path):
    out_short = os.path.join(tmp_path, "short.mp4")
    config = RenderConfig(target_width=1080, target_height=1920, crop_mode=CropMode.BLUR_BACKGROUND)
    
    await ffmpeg_engine.render_shorts_vertical(sample_video, out_short, config)
    assert os.path.exists(out_short)
    
    out_meta = await ffmpeg_engine.probe_service.probe(out_short, use_cache=False)
    assert out_meta.primary_video_stream.width == 1080
    assert out_meta.primary_video_stream.height == 1920
  
