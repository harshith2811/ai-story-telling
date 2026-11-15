"""
Automated Tests for Voice Generation, English & Telugu Support, and Caching
"""

import pytest
from pathlib import Path
from app.services.voice_engine.voice_service import VoiceService, VOICE_REGISTRY


def test_voice_registry_multilingual():
    """Verify registry includes both English and Telugu neural voices."""
    service = VoiceService()
    voices_en = service.list_voices(language="English")
    voices_te = service.list_voices(language="Telugu")

    assert len(voices_en) >= 2
    assert len(voices_te) >= 2

    # Check Telugu speakers
    telugu_ids = [v["id"] for v in voices_te]
    assert "te-IN-MohanNeural" in telugu_ids or "te-IN-ShrutiNeural" in telugu_ids


@pytest.mark.asyncio
async def test_speech_generation_and_duration():
    """Verify speech audio file generation and accurate duration tracking."""
    service = VoiceService()
    text = "StoryForge AI delivers cinematic vertical video experiences."

    audio_path, duration = await service.generate_speech(
        text=text,
        language="English",
        speed=1.0,
    )

    assert audio_path.exists()
    assert audio_path.stat().st_size > 0
    assert duration > 0.5
