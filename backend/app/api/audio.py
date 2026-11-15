"""
StoryForge AI - Voice & Audio Narration API Router
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.project import Project, ProjectStatus, Scene
from app.schemas.project import SceneResponse
from app.services.voice_engine import VoiceService
from app.services.music_engine.music_service import MusicService

logger = logging.getLogger(__name__)

router = APIRouter()


class VoicePreviewRequest(BaseModel):
    voice_id: str
    sample_text: Optional[str] = None
    language: str = "English"
    speed: float = 1.0


@router.get("/voices")
async def list_voices(language: Optional[str] = None) -> Any:
    """List supported voices, including English and Telugu neural voices."""
    service = VoiceService()
    return service.list_voices(language=language)


@router.get("/music")
async def list_music_tracks() -> Any:
    """List available background music soundtracks and moods."""
    service = MusicService()
    tracks = service.list_available_tracks()
    return [
        {
            **t,
            "audio_url": f"/static/assets/music/{t['filename']}",
        }
        for t in tracks
    ]


@router.get("/music/preview/{mood}")
async def preview_music_mood(mood: str) -> Any:
    """Get the audio URL for a specific background soundtrack mood."""
    service = MusicService()
    track_path = service.get_track_for_mood(mood)
    if not track_path or not track_path.exists():
        raise HTTPException(status_code=404, detail=f"No music track found for mood: {mood}")
    return {
        "mood": mood,
        "filename": track_path.name,
        "audio_url": f"/static/assets/music/{track_path.name}",
    }


@router.post("/preview")
async def preview_voice(payload: VoicePreviewRequest) -> Any:
    """Generate or retrieve a quick speech audio preview."""
    service = VoiceService()
    text = payload.sample_text
    if not text:
        if "telugu" in payload.language.lower():
            text = "నమస్కారం, ఇది స్టోరీఫోర్జ్ AI స్వర నమూనా."
        else:
            text = "Welcome to StoryForge AI. Your inspiring journey starts right now."

    audio_path, duration = await service.generate_speech(
        text=text,
        voice_id=payload.voice_id,
        language=payload.language,
        speed=payload.speed,
    )
    return {
        "audio_url": f"/static/assets/audio/{audio_path.name}",
        "duration": duration,
        "voice_id": payload.voice_id,
    }


@router.post("/generate/{scene_id}", response_model=SceneResponse)
async def generate_scene_audio(
    scene_id: int,
    voice_id: Optional[str] = None,
    speed: float = 1.0,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate narration audio for an individual scene."""
    stmt = select(Scene).where(Scene.id == scene_id)
    result = await db.execute(stmt)
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Fetch project language
    proj_stmt = select(Project).where(Project.id == sc.project_id)
    proj_res = await db.execute(proj_stmt)
    proj = proj_res.scalar_one_or_none()
    lang = proj.language if proj else "English"

    service = VoiceService()
    audio_path, duration = await service.generate_speech(
        text=sc.narration,
        voice_id=voice_id,
        language=lang,
        speed=speed,
    )

    sc.audio_path = str(audio_path)
    sc.duration = round(duration, 1)
    await db.commit()
    await db.refresh(sc)
    return sc


@router.post("/generate-all/{project_id}", response_model=list[SceneResponse])
async def generate_all_project_audio(
    project_id: int,
    voice_id: Optional[str] = None,
    speed: float = 1.0,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate audio narration for every scene in a project."""
    stmt = select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_number)
    result = await db.execute(stmt)
    scenes = result.scalars().all()
    if not scenes:
        raise HTTPException(status_code=404, detail="No scenes found for project")

    proj_stmt = select(Project).where(Project.id == project_id)
    proj_res = await db.execute(proj_stmt)
    proj = proj_res.scalar_one_or_none()
    lang = proj.language if proj else "English"

    service = VoiceService()
    for sc in scenes:
        audio_path, duration = await service.generate_speech(
            text=sc.narration,
            voice_id=voice_id,
            language=lang,
            speed=speed,
        )
        sc.audio_path = str(audio_path)
        sc.duration = round(duration, 1)

    if proj:
        proj.status = ProjectStatus.AUDIO_READY

    await db.commit()
    for sc in scenes:
        await db.refresh(sc)
    return scenes
