"""
StoryForge AI - Storyboard Scenes API Router
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.project import Scene
from app.schemas.project import SceneResponse, SceneUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/project/{project_id}", response_model=list[SceneResponse])
async def list_project_scenes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all scenes belonging to a project."""
    stmt = select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_number)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: int,
    payload: SceneUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update a scene's narration, visual prompt, camera movement, or duration."""
    stmt = select(Scene).where(Scene.id == scene_id)
    result = await db.execute(stmt)
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="Scene not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(sc, field, val)

    await db.commit()
    await db.refresh(sc)
    return sc
