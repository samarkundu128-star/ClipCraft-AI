telegram_video_bot/
│
├── config.py             # Settings, Env variables, API keys
├── main.py               # Telegram Bot entry point
├── requirements.txt      # Dependency list
│
├── ai/                   # AI Brain Modules
│   ├── gemini_engine.py  # Gemini API logic (Highlights, Hooks, Captions)
│   ├── whisper_engine.py # Speech-to-Text Transcription
│   └── vision_engine.py  # OpenCV Face Tracking & Scene Detection
│
├── media/                # Video Processing Engine
│   ├── ffmpeg_core.py    # Fast FFmpeg slicing, joining, rendering
│   ├── moviepy_editor.py # Complex overlays, beat sync & transitions
│   └── thumbnail.py      # Pillow/ImageMagick thumbnail generator
│
├── utils/                # Queue, Cleanup, Error Handlers
│   ├── task_queue.py     # Background worker queue (Celery/Asyncio)
│   └── file_manager.py   # Auto temp-file cleanup & disk management
│
└── downloads/            # Temporary storage (Auto-cleaned)
