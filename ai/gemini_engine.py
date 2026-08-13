import google.generativeai as genai
import json
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

class GeminiEngine:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def analyze_content(self, transcript_text: str):
        prompt = f"""
        You are an expert short-form video editor for TikTok, Instagram Reels, and YouTube Shorts.
        Analyze the following video transcript with timestamps and extract the single most engaging/viral 30 to 60-second clip.

        Transcript:
        {transcript_text}

        Return strictly JSON output in this format:
        {{
            "start_time": "00:01:15",
            "end_time": "00:01:45",
            "viral_score": 92,
            "hook_text": "Stop doing this mistake!",
            "title": "The Ultimate Productivity Hack",
            "caption": "You won't believe how much time this saves 🚀 #productivity #lifehacks",
            "editing_style": "fast_paced_zoom"
        }}
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            # Graceful Fallback if API fails
            print(f"[Gemini Error]: {e}. Triggering fallback local engine.")
            return {
                "start_time": "00:00:00",
                "end_time": "00:00:30",
                "viral_score": 50,
                "hook_text": "Watch This!",
                "title": "Processed Video",
                "caption": "#shorts #viral",
                "editing_style": "default"
            }
          
