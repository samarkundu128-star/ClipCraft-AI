ClipCraft-AI/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── run.py                       # Production Entry Point
│
├── app/
│   ├── __init__.py
│   ├── config.py                # Environment & Path configurations
│   ├── main.py                  # Bot Application Initializer
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── gemini_engine.py     # Content Analysis & Viral Selection
│   │   ├── whisper_engine.py    # Speech-to-Text Transcription
│   │   └── vision_engine.py     # OpenCV Face Tracking / Crop logic
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py             # Basic Commands (/start, /help)
│   │   └── upload.py            # Video Upload & Processing Trigger
│   │
│   ├── media/
│   │   ├── __init__.py
│   │   ├── ffmpeg_core.py       # Raw Subprocess Execution (Fast)
│   │   ├── moviepy_editor.py   # Overlay Effects & Text Generation
│   │   └── subtitle_engine.py  # SRT/ASS Subtitle Burner
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── video_pipeline.py    # Orchestrator connecting AI + Media + Telegram
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py     # Disk Cleanup & Storage Guards
│       ├── logger.py           # Structured Logging Setup
│       └── task_queue.py       # Async Processing Queue
│
├── downloads/                   # Ignored by Git
└── outputs/                     # Ignored by Git
