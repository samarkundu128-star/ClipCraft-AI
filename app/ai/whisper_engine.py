import logging
import whisper

logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self, model_size: str = "tiny"):
        """
        Whisper STT Engine Initializer
        Render Free Tier (512MB RAM) ke liye default 'tiny' model best hai.
        """
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
        """
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
            
