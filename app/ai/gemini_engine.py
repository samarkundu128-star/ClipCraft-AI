import google.generativeai as genai
import json
import time
from app.config import GEMINI_API_KEY
from app.utils.logger import logger

genai.configure(api_key=GEMINI_API_KEY)

class GeminiEngine:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def analyze_viral_moments(self, transcript_text: str, max_retries: int = 3) -> dict:
        prompt = f"""
        You are an expert short-form video editor. Analyze this video transcript with timestamps.
        Find the single most engaging/viral segment (duration between 30 to 60 seconds).

        Transcript:
        {transcript_text}

        Return STRICTLY valid JSON with no markdown formatting outside JSON:
        {{
            "start_time": "00:01:10",
            "end_time": "00:01:40",
            "viral_score": 92,
            "title": "Viral Moment Title",
            "caption": "Check this out! #shorts #viral",
            "hook_text": "Watch until the end!"
        }}
        """

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                return json.loads(response.text)
            except Exception as e:
                logger.warning(f"[Gemini Attempt {attempt + 1}] Failed: {e}")
                time.sleep(2 ** attempt)  # Exponential Backoff

        # Fallback Engine Response
        logger.error("[Gemini Engine] All retries failed. Returning default fallback segment.")
        return {
            "start_time": "00:00:00",
            "end_time": "00:00:30",
            "viral_score": 50,
            "title": "Automated Short Clip",
            "caption": "#shorts #ai",
            "hook_text": "Watch this!"
        }
      
