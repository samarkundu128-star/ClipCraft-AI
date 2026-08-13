import json
import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiEngine:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze_viral_moments(self, transcript_text: str) -> dict:
        prompt = f"""
        Analyze this transcript and find the single most viral 30-60 sec moment.
        
        Transcript: {transcript_text}

        Return strictly valid JSON:
        {{
            "start_time": "00:01:10",
            "end_time": "00:01:40",
            "viral_score": 90,
            "title": "Viral Moment Title",
            "caption": "Check this out! #shorts #viral",
            "hook_text": "Watch until the end!"
        }}
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                }
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[Gemini Error]: {e}")
            return {
                "start_time": "00:00:00",
                "end_time": "00:00:30",
                "viral_score": 50,
                "title": "Processed Clip",
                "caption": "#shorts",
                "hook_text": "Watch this"
            }
            
