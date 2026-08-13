# BAD (Will throw ModuleNotFoundError):
# from ai.gemini_engine import GeminiEngine

# GOOD (Use absolute imports from package root or handle sys.path in entry point):
from app.ai.gemini_engine import GeminiEngine
from app.services.video_pipeline import VideoPipeline
from app.utils.logger import logger
