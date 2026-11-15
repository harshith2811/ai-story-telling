"""
StoryForge AI - Story Generation & Hook Intelligence API Router
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.project import Character, Project, ProjectStatus, Scene
from app.schemas.project import ProjectResponse, StoryGenerateRequest
from app.services.character_engine import CharacterService
from app.services.hook_engine import HookEvaluator, StoryQualityEvaluator
from app.services.storyboard_engine import StoryboardService
from app.services.story_engine import StoryEngine, get_llm_provider

logger = logging.getLogger(__name__)

router = APIRouter()


class HookGenerateRequest(BaseModel):
    title: str
    topic: str
    original_hook: str
    story_summary: str


class HookEvaluateRequest(BaseModel):
    hook_text: str
    topic: str


class StoryAuditRequest(BaseModel):
    title: str
    duration: float = 60.0
    story_script: str
    scenes: list[dict[str, Any]] = []


class UserStoryInputRequest(BaseModel):
    story_text: str = Field(..., min_length=10, description="Full raw story narrative provided by the user")
    title: Optional[str] = None
    genre: Optional[str] = "Cinematic Drama"
    visual_style: Optional[str] = "Cinematic realism"
    language: str = "English"
    duration: float = Field(60.0, ge=5.0, le=600.0)
    emotional_tone: str = "engaging"
    audience: str = "general"
    narrator: Optional[str] = None


class StoryRewriteRequest(BaseModel):
    current_text: str
    story_context: str
    revision_goal: str


@router.post("/generate", response_model=ProjectResponse)
async def generate_story_endpoint(
    payload: StoryGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate a multi-scene, emotionally compelling story script and initialize project."""
    logger.info("Initiating story generation: %s (%s)", payload.topic, payload.language)

    provider = get_llm_provider()
    story_engine = StoryEngine(provider=provider)
    char_service = CharacterService()
    storyboard_service = StoryboardService()
    hook_evaluator = HookEvaluator(provider=provider)
    quality_evaluator = StoryQualityEvaluator(provider=provider)

    # 1. Generate core structured story
    story_dict = await story_engine.generate_story({
        "topic": payload.topic,
        "category": payload.category or "inspirational",
        "language": payload.language,
        "duration": int(payload.duration),
        "emotional_tone": payload.emotional_tone,
        "audience": payload.audience,
    })

    # 2. Extract & enrich character consistency profiles
    characters_meta = char_service.extract_characters_from_story(story_dict)

    # 3. Build storyboard with cinematography directives
    storyboard_scenes = storyboard_service.build_storyboard_from_story(
        story_dict, character_profiles=characters_meta
    )

    # 4. Generate & score alternative hooks
    alt_hooks = await hook_evaluator.generate_alternative_hooks(
        title=story_dict.get("title", ""),
        topic=payload.topic,
        original_hook=story_dict.get("hook", ""),
        story_summary=story_dict.get("story", "")[:200],
    )
    hook_eval = await hook_evaluator.evaluate_hook(
        hook_text=story_dict.get("hook", ""), topic=payload.topic
    )

    # 5. Quality audit
    quality_audit = await quality_evaluator.audit_story(
        title=story_dict.get("title", ""),
        duration=payload.duration,
        story_script=story_dict.get("story", ""),
        scenes=storyboard_scenes,
    )

    # 6. Save to Database
    story_metadata = {
        "title": story_dict.get("title"),
        "hook": story_dict.get("hook"),
        "story": story_dict.get("story"),
        "moral": story_dict.get("moral"),
        "estimated_duration": story_dict.get("estimated_duration", payload.duration),
        "alternative_hooks": alt_hooks,
        "hook_evaluation": hook_eval,
        "quality_audit": quality_audit,
    }

    proj = Project(
        title=story_dict.get("title", "Untitled Story"),
        topic=payload.topic,
        category=payload.category,
        language=payload.language,
        duration_target=payload.duration,
        emotional_tone=payload.emotional_tone,
        audience=payload.audience,
        visual_style=payload.visual_style,
        narrator=payload.narrator,
        status=ProjectStatus.STORY_READY,
        story_json=json.dumps(story_metadata),
    )
    db.add(proj)
    await db.flush()

    # Save scenes
    for sc in storyboard_scenes:
        scene_row = Scene(
            project_id=proj.id,
            scene_number=sc["scene_number"],
            narration=sc["narration"],
            emotion=sc.get("emotion"),
            visual_prompt=sc.get("visual_prompt"),
            duration=sc.get("duration", 5.0),
            camera_movement=sc.get("camera_movement", "slow_zoom_in"),
            music_mood=sc.get("music_mood", "Inspirational"),
        )
        db.add(scene_row)

    # Save characters
    for ch in characters_meta:
        char_row = Character(
            project_id=proj.id,
            name=ch.get("name", "Protagonist"),
            description=ch.get("role", "Protagonist"),
            visual_description=ch.get("visual_description"),
            reference_image_path=ch.get("reference_image_path"),
        )
        db.add(char_row)

    await db.commit()
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes), selectinload(Project.characters))
        .where(Project.id == proj.id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.post("/analyze-user-story", response_model=ProjectResponse)
async def analyze_user_story_endpoint(
    payload: UserStoryInputRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Analyze a user-provided story narrative into a deep structured cinematic production."""
    logger.info("Deep story analysis requested for user story (%d characters)...", len(payload.story_text))

    from app.services.story_engine.story_analyzer import StoryAnalyzer
    provider = get_llm_provider()
    analyzer = StoryAnalyzer(provider=provider)
    char_service = CharacterService()

    # 1. Deep story decomposition
    blueprint = await analyzer.analyze_story(
        story_text=payload.story_text,
        title=payload.title,
        genre=payload.genre or payload.emotional_tone,
        visual_style=payload.visual_style or "Cinematic realism",
        duration=int(payload.duration),
    )

    title = blueprint.get("story_title", payload.title or "The Cinematic Story")
    scenes = blueprint.get("scenes", [])
    character_bible = blueprint.get("character_bible", [])

    # 2. Persist Project
    proj = Project(
        title=title,
        topic=payload.story_text[:200],
        category=blueprint.get("genre", "Storytelling"),
        language=payload.language,
        duration_target=payload.duration,
        emotional_tone=payload.emotional_tone,
        audience=payload.audience,
        visual_style=payload.visual_style,
        narrator=payload.narrator,
        status=ProjectStatus.STORY_READY,
        story_json=json.dumps(blueprint),
    )
    db.add(proj)
    await db.flush()

    # 3. Save permanent Character Bible
    char_service.save_character_bible(proj.id, character_bible)

    # 4. Save Scenes
    for sc in scenes:
        scene_row = Scene(
            project_id=proj.id,
            scene_number=sc["scene_number"],
            narration=sc["narration"],
            emotion=sc.get("emotion"),
            visual_prompt=sc.get("visual_prompt") or sc.get("image_prompt"),
            duration=sc.get("duration", 5.0),
            camera_movement=sc.get("camera_movement", "slow_zoom_in"),
            music_mood=sc.get("emotion", "Suspense"),
        )
        db.add(scene_row)

    # 5. Save Character records
    for ch in character_bible:
        char_row = Character(
            project_id=proj.id,
            name=ch.get("name", "Character"),
            description=ch.get("role", "Protagonist"),
            visual_description=ch.get("visual_identity_description") or ch.get("clothing"),
            reference_image_path=ch.get("reference_image_path"),
        )
        db.add(char_row)

    await db.commit()
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes), selectinload(Project.characters))
        .where(Project.id == proj.id)
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.post("/hooks/alternative")
async def generate_alternative_hooks_endpoint(payload: HookGenerateRequest) -> Any:
    """Generate 3 alternative opening hooks."""
    evaluator = HookEvaluator()
    return await evaluator.generate_alternative_hooks(
        title=payload.title,
        topic=payload.topic,
        original_hook=payload.original_hook,
        story_summary=payload.story_summary,
    )


@router.post("/hooks/evaluate")
async def evaluate_hook_endpoint(payload: HookEvaluateRequest) -> Any:
    """Score a hook on a transparent 0-100 retention scale."""
    evaluator = HookEvaluator()
    return await evaluator.evaluate_hook(hook_text=payload.hook_text, topic=payload.topic)


@router.post("/audit")
async def audit_story_endpoint(payload: StoryAuditRequest) -> Any:
    """Perform a comprehensive storytelling quality audit."""
    evaluator = StoryQualityEvaluator()
    return await evaluator.audit_story(
        title=payload.title,
        duration=payload.duration,
        story_script=payload.story_script,
        scenes=payload.scenes,
    )


@router.post("/rewrite")
async def rewrite_story_section_endpoint(payload: StoryRewriteRequest) -> Any:
    """Rewrite a paragraph or sentence for greater emotional resonance."""
    evaluator = StoryQualityEvaluator()
    return await evaluator.rewrite_section(
        current_text=payload.current_text,
        story_context=payload.story_context,
        revision_goal=payload.revision_goal,
    )
