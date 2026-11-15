"""
StoryForge AI - Projects API Router
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.project import Character, Project, ProjectStatus, Scene
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Retrieve all projects ordered by newest first."""
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes), selectinload(Project.characters))
        .order_by(desc(Project.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new project record."""
    proj = Project(
        title=payload.title,
        topic=payload.topic,
        category=payload.category,
        language=payload.language,
        duration_target=payload.duration_target,
        emotional_tone=payload.emotional_tone,
        audience=payload.audience,
        visual_style=payload.visual_style,
        narrator=payload.narrator,
        status=ProjectStatus.DRAFT,
    )
    db.add(proj)
    await db.commit()
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes), selectinload(Project.characters))
        .where(Project.id == proj.id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get project details including all scenes and characters."""
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes), selectinload(Project.characters))
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update project metadata or story script."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(proj, field, val)

    await db.commit()
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes), selectinload(Project.characters))
        .where(Project.id == project_id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project and cascade all scenes, characters, and renders."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(proj)
    await db.commit()
