import logging
import whisper

logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self, model_size: str = "tiny"):
        logger.info(f"Loading Whisper model: {model_size}...")
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully!")

    def transcribe(self, audio_path: str):
        logger.info(f"Starting transcription for: {audio_path}")
        # fp16=False CPU execution me error aur crash rokta hai
        result = self.model.transcribe(audio_path, fp16=False)
        return result
        
