"""
StoryForge AI - Scene Images API Router
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.project import Project, ProjectStatus, Scene
from app.schemas.project import SceneResponse
from app.services.image_engine import ImageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate/{scene_id}", response_model=SceneResponse)
async def generate_scene_image_endpoint(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate or regenerate image for an individual scene."""
    stmt = select(Scene).where(Scene.id == scene_id)
    result = await db.execute(stmt)
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Fetch project for visual_style
    proj_stmt = select(Project).where(Project.id == sc.project_id)
    proj_res = await db.execute(proj_stmt)
    project = proj_res.scalar_one_or_none()

    from app.services.character_engine import CharacterService
    char_service = CharacterService()
    bible = char_service.load_character_bible(sc.project_id)

    image_service = ImageService()
    img_path = await image_service.generate_scene_image(
        prompt=sc.visual_prompt or f"Cinematic {sc.emotion or 'Inspirational'} scene",
        scene_number=sc.scene_number,
        project_id=sc.project_id,
        emotion=sc.emotion or "Inspirational",
        character_bible=bible,
        visual_style=project.visual_style if project else "cinematic_realism",
        scene_data={
            "visual_prompt": sc.visual_prompt,
            "narration": sc.narration,
            "action": sc.narration,
            "emotion": sc.emotion,
        },
        force_regenerate=True,
    )

    sc.image_path = str(img_path)
    await db.commit()
    await db.refresh(sc)
    return sc


@router.post("/generate-all/{project_id}", response_model=list[SceneResponse])
async def generate_all_project_images(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate images for all scenes in a project."""
    stmt = select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_number)
    result = await db.execute(stmt)
    scenes = result.scalars().all()
    if not scenes:
        raise HTTPException(status_code=404, detail="No scenes found for project")

    proj_stmt = select(Project).where(Project.id == project_id)
    proj_res = await db.execute(proj_stmt)
    proj = proj_res.scalar_one_or_none()

    from app.services.character_engine import CharacterService
    char_service = CharacterService()
    bible = char_service.load_character_bible(project_id)

    image_service = ImageService()
    prev_scene_dict = None
    for sc in scenes:
        sc_dict = {
            "visual_prompt": sc.visual_prompt,
            "narration": sc.narration,
            "action": sc.narration,
            "emotion": sc.emotion,
        }
        img_path = await image_service.generate_scene_image(
            prompt=sc.visual_prompt or f"Cinematic {sc.emotion or 'Inspirational'} scene",
            scene_number=sc.scene_number,
            project_id=project_id,
            emotion=sc.emotion or "Inspirational",
            character_bible=bible,
            visual_style=proj.visual_style if proj else "cinematic_realism",
            scene_data=sc_dict,
            previous_scene=prev_scene_dict,
        )
        sc.image_path = str(img_path)
        prev_scene_dict = sc_dict

    if proj:
        proj.status = ProjectStatus.IMAGES_READY

    await db.commit()
    for sc in scenes:
        await db.refresh(sc)
    return scenes
