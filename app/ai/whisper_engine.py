import logging
import os
import whisper

logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self, model_size: str = "tiny"):
        logger.info(f"Loading Whisper model: {model_size}...")
        try:
            self.model = whisper.load_model(model_size)
            logger.info("Whisper model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise e

    def transcribe(self, audio_path: str) -> dict:
        """
        Audio file ko text me transcribe karta hai.
        Auto-corrects .mp3 extension to .wav if needed.
        """
        # Agar passed file path .mp3 hai lekin file disk par .wav format me exist karti hai
        if not os.path.exists(audio_path) and audio_path.endswith(".mp3"):
            wav_path = audio_path[:-4] + ".wav"
            if os.path.exists(wav_path):
                audio_path = wav_path

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")

        try:
            logger.info(f"Starting transcription for: {audio_path}")
            result = self.model.transcribe(audio_path)
            
            transcript_text = result.get("text", "").strip()
            logger.info("Transcription completed successfully.")
            
            return {
                "text": transcript_text,
                "segments": result.get("segments", [])
            }
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {
                "text": "",
                "segments": [],
                "error": str(e)
            }
            
