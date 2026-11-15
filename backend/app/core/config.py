"""
StoryForge AI - Application Settings

Centralized configuration using Pydantic BaseSettings.
All values are overridable via environment variables.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables with sensible defaults."""

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "StoryForge AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./storyforge.db"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    )

    # ── LLM Provider (Frontier Strong Script Models) ─────────────────────
    LLM_PROVIDER: str = "gemini"  # gemini | groq | openrouter | openai | anthropic | ollama | heuristic
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.3"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # ── TTS Provider ────────────────────────────────────────────────────
    TTS_PROVIDER: str = "edge_tts"  # edge_tts | piper | elevenlabs
    PIPER_PATH: Optional[str] = None
    PIPER_MODEL: str = "en_US-lessac-medium"
    EDGE_TTS_ENABLED: bool = True
    EDGE_TTS_VOICE: str = "en-US-GuyNeural"
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = None

    # ── Image Provider ──────────────────────────────────────────────────
    IMAGE_PROVIDER: str = "cloudflare"  # cloudflare | pollinations | comfyui | procedural
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    CLOUDFLARE_API_TOKEN: Optional[str] = None
    COMFYUI_URL: str = "http://localhost:8188"
    SD_API_URL: str = "http://localhost:7860"
    OPENAI_IMAGE_MODEL: str = "dall-e-3"
    DEFAULT_IMAGE_WIDTH: int = 1080
    DEFAULT_IMAGE_HEIGHT: int = 1920

    # ── YouTube API ─────────────────────────────────────────────────────
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/v1/youtube/callback"

    # ── Storage Paths ───────────────────────────────────────────────────
    BASE_DIR: str = str(Path(__file__).resolve().parent.parent.parent)
    STORAGE_DIR: str = "storage"
    ASSETS_DIR: str = "storage/assets"
    OUTPUTS_DIR: str = "storage/outputs"
    TEMP_DIR: str = "storage/temp"
    IMAGES_DIR: str = "storage/assets/images"
    AUDIO_DIR: str = "storage/assets/audio"
    MUSIC_DIR: str = "storage/assets/music"
    RENDERS_DIR: str = "storage/outputs/renders"
    THUMBNAILS_DIR: str = "storage/outputs/thumbnails"
    LOGS_DIR: str = "logs"

    # ── Concurrency ─────────────────────────────────────────────────────
    MAX_CONCURRENT_JOBS: int = 3
    JOB_TIMEOUT_SECONDS: int = 3600

    # ── Video Defaults ──────────────────────────────────────────────────
    DEFAULT_VIDEO_RESOLUTION: str = "1080x1920"  # 9:16 vertical Shorts format
    DEFAULT_VIDEO_FPS: int = 30
    DEFAULT_VIDEO_FORMAT: str = "mp4"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @property
    def storage_path(self) -> Path:
        return Path(self.BASE_DIR) / self.STORAGE_DIR

    @property
    def assets_path(self) -> Path:
        return Path(self.BASE_DIR) / self.ASSETS_DIR

    @property
    def outputs_path(self) -> Path:
        return Path(self.BASE_DIR) / self.OUTPUTS_DIR

    @property
    def temp_path(self) -> Path:
        return Path(self.BASE_DIR) / self.TEMP_DIR

    @property
    def logs_path(self) -> Path:
        return Path(self.BASE_DIR) / self.LOGS_DIR

    def get_all_storage_dirs(self) -> list[Path]:
        """Return all directories that should be created at startup."""
        base = Path(self.BASE_DIR)
        return [
            base / self.STORAGE_DIR,
            base / self.ASSETS_DIR,
            base / self.OUTPUTS_DIR,
            base / self.TEMP_DIR,
            base / self.IMAGES_DIR,
            base / self.AUDIO_DIR,
            base / self.MUSIC_DIR,
            base / self.RENDERS_DIR,
            base / self.THUMBNAILS_DIR,
            base / self.LOGS_DIR,
        ]


# Global settings singleton
settings = Settings()
