"""
StoryForge AI - Project Models

SQLAlchemy ORM models for projects, scenes, characters, and video renders.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProjectStatus(str, enum.Enum):
    """Lifecycle status of a project."""
    DRAFT = "draft"
    STORY_GENERATING = "story_generating"
    STORY_READY = "story_ready"
    IMAGES_GENERATING = "images_generating"
    IMAGES_READY = "images_ready"
    AUDIO_GENERATING = "audio_generating"
    AUDIO_READY = "audio_ready"
    RENDERING = "rendering"
    COMPLETED = "completed"
    PUBLISHED = "published"
    FAILED = "failed"


class RenderStatus(str, enum.Enum):
    """Status of a video render job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    """Top-level project representing a single video production."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    topic = Column(String(1000), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False, index=True)
    category = Column(String(200), nullable=True)
    language = Column(String(50), default="English", nullable=False)
    duration_target = Column(Float, default=60.0, nullable=False)  # seconds
    emotional_tone = Column(String(200), default="engaging", nullable=False)
    audience = Column(String(200), default="general", nullable=False)
    visual_style = Column(String(200), default="cinematic", nullable=False)
    narrator = Column(String(200), nullable=True)
    story_json = Column(Text, nullable=True)  # Full structured story as JSON
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_number")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    renders = relationship("VideoRender", back_populates="project", cascade="all, delete-orphan")
    analytics = relationship("VideoAnalytics", back_populates="project", cascade="all, delete-orphan")
    generation_history = relationship("GenerationHistory", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title='{self.title}', status={self.status})>"


class Scene(Base):
    """A single scene within a project video."""
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_number = Column(Integer, nullable=False)
    narration = Column(Text, nullable=False)
    emotion = Column(String(200), nullable=True)
    visual_prompt = Column(Text, nullable=True)
    image_path = Column(String(1000), nullable=True)
    audio_path = Column(String(1000), nullable=True)
    duration = Column(Float, nullable=True)  # seconds
    camera_movement = Column(String(200), default="slow_zoom_in", nullable=True)
    music_mood = Column(String(200), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="scenes")

    def __repr__(self) -> str:
        return f"<Scene(id={self.id}, project_id={self.project_id}, number={self.scene_number})>"


class Character(Base):
    """A character referenced across scenes for visual consistency."""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    visual_description = Column(Text, nullable=True)
    reference_image_path = Column(String(1000), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="characters")

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name='{self.name}')>"


class VideoRender(Base):
    """Tracks a video render job and its output."""
    __tablename__ = "video_renders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(RenderStatus), default=RenderStatus.QUEUED, nullable=False, index=True)
    output_path = Column(String(1000), nullable=True)
    resolution = Column(String(50), default="1080x1920", nullable=False)
    fps = Column(Integer, default=30, nullable=False)
    format = Column(String(20), default="mp4", nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="renders")

    def __repr__(self) -> str:
        return f"<VideoRender(id={self.id}, project_id={self.project_id}, status={self.status})>"
