"""
StoryForge AI - System Diagnostics & Service Status API Router
"""

from __future__ import annotations

import logging
from pathlib import Path
import shutil
import subprocess
from typing import Any

from fastapi import APIRouter
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/diagnostics")
async def get_system_diagnostics() -> dict[str, Any]:
    """Inspect installation status of all pipeline components and external services."""
    # 1. FFmpeg inspection
    ffmpeg_installed = shutil.which("ffmpeg") is not None
    ffmpeg_version = "Not found"
    if ffmpeg_installed:
        try:
            res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
            ffmpeg_version = res.stdout.splitlines()[0]
        except Exception:
            ffmpeg_version = "Installed (Version check error)"

    # 2. Ollama / Local LLM check
    ollama_online = False
    ollama_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if res.status_code == 200:
                ollama_online = True
                ollama_models = [m["name"] for m in res.json().get("models", [])]
    except Exception:
        pass

    # 3. ComfyUI check
    comfyui_online = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.COMFYUI_URL}/system_stats")
            if res.status_code == 200:
                comfyui_online = True
    except Exception:
        pass

    # 4. TTS check
    edge_tts_available = settings.EDGE_TTS_ENABLED

    # 5. Whisper check
    whisper_available = True
    try:
        import faster_whisper
    except ImportError:
        whisper_available = False

    # 6. YouTube API credentials
    youtube_configured = bool(settings.YOUTUBE_CLIENT_ID and settings.YOUTUBE_CLIENT_SECRET)

    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": {
            "debug": settings.DEBUG,
            "database_url": settings.DATABASE_URL,
            "storage_path": str(settings.storage_path.resolve()),
        },
        "services": {
            "ffmpeg": {
                "installed": ffmpeg_installed,
                "version": ffmpeg_version,
                "required": True,
                "status": "ready" if ffmpeg_installed else "missing",
            },
            "llm_engine": {
                "provider": settings.LLM_PROVIDER,
                "ollama_online": ollama_online,
                "ollama_models": ollama_models,
                "gemini_configured": bool(settings.GEMINI_API_KEY),
                "groq_configured": bool(settings.GROQ_API_KEY),
                "openai_configured": bool(settings.OPENAI_API_KEY),
                "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
                "status": "ready",
            },
            "voice_tts": {
                "provider": "edge_tts",
                "available": edge_tts_available,
                "telugu_support": True,
                "english_support": True,
                "status": "ready",
            },
            "speech_alignment": {
                "provider": "faster_whisper",
                "available": whisper_available,
                "status": "ready" if whisper_available else "missing",
            },
            "image_generation": {
                "provider": settings.IMAGE_PROVIDER,
                "comfyui_online": comfyui_online,
                "procedural_fallback_ready": True,
                "status": "ready (flux + procedural)",
            },
            "youtube_publishing": {
                "configured": youtube_configured,
                "client_id_present": bool(settings.YOUTUBE_CLIENT_ID),
                "status": "configured" if youtube_configured else "ready_for_manual_export",
            },
        },
    }


@router.get("/ai-config")
async def get_ai_config() -> dict[str, Any]:
    """Retrieve current LLM scriptwriting configuration and available providers."""
    return {
        "active_provider": settings.LLM_PROVIDER,
        "image_provider": settings.IMAGE_PROVIDER,
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "model": settings.GEMINI_MODEL,
            "is_free": True,
            "tier": "Frontier (Recommended for viral stories & bilingual Telugu)",
        },
        "groq": {
            "configured": bool(settings.GROQ_API_KEY),
            "model": settings.GROQ_MODEL,
            "is_free": True,
            "tier": "Ultra-Fast Llama 3.3 70B (300 tokens/sec)",
        },
        "openrouter": {
            "configured": bool(settings.OPENROUTER_API_KEY),
            "model": settings.OPENROUTER_MODEL,
            "is_free": True,
            "tier": "Free DeepSeek R1 & Llama 70B",
        },
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY),
            "model": settings.OPENAI_MODEL,
            "is_free": False,
            "tier": "GPT-4o",
        },
        "ollama": {
            "url": settings.OLLAMA_URL,
            "model": settings.OLLAMA_MODEL,
            "is_free": True,
            "tier": "Local (Qwen 2.5 14B / Llama 3.3)",
        },
    }


@router.post("/ai-config")
async def update_ai_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Dynamically update LLM provider, image engine, and API keys."""
    if "provider" in payload and payload["provider"]:
        settings.LLM_PROVIDER = payload["provider"]
    if "image_provider" in payload and payload["image_provider"]:
        settings.IMAGE_PROVIDER = payload["image_provider"]
    if "gemini_api_key" in payload:
        settings.GEMINI_API_KEY = payload["gemini_api_key"].strip() or None
    if "groq_api_key" in payload:
        settings.GROQ_API_KEY = payload["groq_api_key"].strip() or None
    if "openrouter_api_key" in payload:
        settings.OPENROUTER_API_KEY = payload["openrouter_api_key"].strip() or None
    if "openai_api_key" in payload:
        settings.OPENAI_API_KEY = payload["openai_api_key"].strip() or None
    if "ollama_model" in payload:
        settings.OLLAMA_MODEL = payload["ollama_model"].strip()

    return {
        "status": "updated",
        "active_provider": settings.LLM_PROVIDER,
        "image_provider": settings.IMAGE_PROVIDER,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY),
    }
