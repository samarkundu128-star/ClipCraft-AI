import whisper

class WhisperEngine:
    def __init__(self, model_size="base"):
        # CPU/GPU ke according auto-load hoga
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str) -> dict:
        result = self.model.transcribe(audio_path, word_timestamps=True)
        return {
            "text": result.get("text", ""),
            "segments": result.get("segments", [])
        }
      
