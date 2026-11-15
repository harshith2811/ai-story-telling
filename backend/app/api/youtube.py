"""
StoryForge AI - YouTube Publishing API Router
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.project import Project, ProjectStatus, VideoRender
from app.services.youtube_engine import YouTubeService

logger = logging.getLogger(__name__)

router = APIRouter()


class PublishRequest(BaseModel):
    project_id: int
    user_approved: bool = False
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None
    privacy_status: str = "private"


@router.get("/metadata/{project_id}")
async def get_publishing_metadata(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate YouTube-optimized title, description, and hashtags for a project."""
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    story_data = {}
    if proj.story_json:
        try:
            story_data = json.loads(proj.story_json)
        except Exception:
            pass

    story_data["title"] = proj.title
    story_data["topic"] = proj.topic

    service = YouTubeService()
    return service.generate_publishing_metadata(story_data, language=proj.language)


@router.post("/publish")
async def publish_video(
    payload: PublishRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Publish video to YouTube with mandatory user approval gate."""
    if not payload.user_approved:
        raise HTTPException(
            status_code=400,
            detail="Publishing requires explicit user confirmation. Set user_approved=True."
        )

    stmt = select(Project).where(Project.id == payload.project_id)
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Locate latest completed render
    render_stmt = select(VideoRender).where(
        VideoRender.project_id == payload.project_id,
        VideoRender.status == "completed"
    )
    render_res = await db.execute(render_stmt)
    render_obj = render_res.scalar_one_or_none()

    if not render_obj or not render_obj.output_path or not Path(render_obj.output_path).exists():
        raise HTTPException(
            status_code=400,
            detail="No completed video render found for this project. Please render first."
        )

    service = YouTubeService()
    meta = service.generate_publishing_metadata({"title": proj.title, "topic": proj.topic}, proj.language)
    if payload.custom_title:
        meta["title"] = payload.custom_title
    if payload.custom_description:
        meta["description"] = payload.custom_description
    meta["privacy_status"] = payload.privacy_status

    result = await service.upload_video(
        video_path=Path(render_obj.output_path),
        metadata=meta,
        user_approved=True,
    )

    proj.status = ProjectStatus.PUBLISHED
    await db.commit()
    return result
