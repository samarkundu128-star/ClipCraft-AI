telegram_video_bot/
│
├── app/
│   ├── main.py                # Telegram bot entry point
│   ├── config.py              # Env vars & settings
│   │
│   ├── handlers/              # Telegram commands & message handlers
│   │   ├── start.py
│   │   ├── upload.py
│   │   ├── link_input.py
│   │   ├── settings.py
│   │   └── status.py
│   │
│   ├── ai/
│   │   ├── gemini_engine.py
│   │   ├── whisper_engine.py
│   │   ├── vision_engine.py
│   │   └── viral_scorer.py
│   │
│   ├── media/
│   │   ├── ffmpeg_core.py
│   │   ├── moviepy_editor.py
│   │   ├── audio_engine.py
│   │   ├── subtitle_engine.py
│   │   └── thumbnail.py
│   │
│   ├── services/              # High-level business logic
│   │   ├── video_pipeline.py
│   │   ├── render_service.py
│   │   ├── delivery_service.py
│   │   └── analytics_service.py
│   │
│   ├── utils/
│   │   ├── task_queue.py
│   │   ├── file_manager.py
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── retry.py
│   │
│   └── templates/
│       ├── hooks/
│       ├── captions/
│       └── subtitle_styles/
│
├── downloads/                 # Temporary input files
├── outputs/                   # Final rendered videos
├── logs/                      # Application logs
├── tests/                     # Unit/integration tests
├── .env
├── .env.example
├── requirements.txt
├── README.md
└── run.py                     # Production launcher
