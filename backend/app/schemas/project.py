"""
StoryForge AI - Project Schemas

Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Character Schemas
# ═══════════════════════════════════════════════════════════════════════════

class CharacterCreate(BaseModel):
    """Schema for creating a new character."""
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    visual_description: Optional[str] = None
    reference_image_path: Optional[str] = None


class CharacterResponse(BaseModel):
    """Schema for character API responses."""
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    visual_description: Optional[str] = None
    reference_image_path: Optional[str] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Scene Schemas
# ═══════════════════════════════════════════════════════════════════════════

class SceneCreate(BaseModel):
    """Schema for creating a scene."""
    scene_number: int = Field(..., ge=1)
    narration: str = Field(..., min_length=1)
    emotion: Optional[str] = None
    visual_prompt: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    duration: Optional[float] = Field(None, ge=0)
    camera_movement: str = "slow_zoom_in"
    music_mood: Optional[str] = None


class SceneUpdate(BaseModel):
    """Schema for updating a scene (all fields optional)."""
    scene_number: Optional[int] = Field(None, ge=1)
    narration: Optional[str] = None
    emotion: Optional[str] = None
    visual_prompt: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    duration: Optional[float] = Field(None, ge=0)
    camera_movement: Optional[str] = None
    music_mood: Optional[str] = None


class SceneResponse(BaseModel):
    """Schema for scene API responses."""
    id: int
    project_id: int
    scene_number: int
    narration: str
    emotion: Optional[str] = None
    visual_prompt: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    camera_movement: Optional[str] = None
    music_mood: Optional[str] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Project Schemas
# ═══════════════════════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    title: str = Field(..., min_length=1, max_length=500)
    topic: str = Field(..., min_length=1, max_length=1000)
    category: Optional[str] = None
    language: str = "English"
    duration_target: float = Field(60.0, ge=5, le=3600)
    emotional_tone: str = "engaging"
    audience: str = "general"
    visual_style: str = "cinematic"
    narrator: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    topic: Optional[str] = Field(None, min_length=1, max_length=1000)
    status: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    duration_target: Optional[float] = Field(None, ge=5, le=3600)
    emotional_tone: Optional[str] = None
    audience: Optional[str] = None
    visual_style: Optional[str] = None
    narrator: Optional[str] = None
    story_json: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project API responses (full detail)."""
    id: int
    title: str
    topic: str
    status: str
    category: Optional[str] = None
    language: str
    duration_target: float
    emotional_tone: str
    audience: str
    visual_style: str
    narrator: Optional[str] = None
    story_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    scenes: list[SceneResponse] = []
    characters: list[CharacterResponse] = []

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    """Schema for paginated project list responses."""
    items: list[ProjectResponse]
    total: int
    page: int = 1
    per_page: int = 20


# ═══════════════════════════════════════════════════════════════════════════
# Story Generation Schemas
# ═══════════════════════════════════════════════════════════════════════════

class StoryGenerateRequest(BaseModel):
    """Schema for requesting AI story generation."""
    topic: str = Field(..., min_length=1, max_length=1000, description="Main topic or idea for the video")
    category: Optional[str] = Field(None, description="Content category (e.g. 'history', 'science', 'horror')")
    language: str = Field("English", description="Language for the narration")
    duration: float = Field(60.0, ge=5, le=3600, description="Target video duration in seconds")
    emotional_tone: str = Field("engaging", description="Desired emotional tone (e.g. 'dramatic', 'calm', 'suspenseful')")
    audience: str = Field("general", description="Target audience (e.g. 'general', 'kids', 'adults')")
    visual_style: str = Field("cinematic", description="Visual style for images (e.g. 'cinematic', 'anime', 'watercolor')")
    narrator: Optional[str] = Field(None, description="Narrator voice style or character name")


class StoryGenerateResponse(BaseModel):
    """Schema for AI-generated story output."""
    project_id: int
    title: str
    scenes: list[SceneResponse]
    characters: list[CharacterResponse]
    story_json: dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════
# Video Render Schemas
# ═══════════════════════════════════════════════════════════════════════════

class VideoRenderRequest(BaseModel):
    """Schema for requesting a video render."""
    project_id: int
    resolution: str = "1080x1920"  # 9:16 vertical Shorts format
    fps: int = Field(30, ge=1, le=120)
    format: str = "mp4"


class VideoRenderResponse(BaseModel):
    """Schema for video render job responses."""
    id: int
    project_id: int
    status: str
    output_path: Optional[str] = None
    resolution: str
    fps: int
    format: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
