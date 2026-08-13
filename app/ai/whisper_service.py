# Updated transcription caller
async def transcribe_media_job(job_id: str, video_path: str):
    audio_path = f"temp/{job_id}/whisper_input.wav"
    
    # FFmpegCore prepares a normalized mono 16kHz WAV file without loading it into Python RAM
    await ffmpeg_engine.extract_whisper_audio(video_path, audio_path)
    
    # Whisper model receives file path directly
    result = await whisper_model.transcribe_async(audio_path)
    return result
  
