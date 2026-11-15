"""
StoryForge AI - Analytics Models

SQLAlchemy ORM models for video analytics and generation history tracking.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class VideoAnalytics(Base):
    """Platform analytics data for a published video."""
    __tablename__ = "video_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(100), default="youtube", nullable=False, index=True)
    video_id = Column(String(200), nullable=True)  # Platform-specific video identifier
    views = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    comments = Column(Integer, default=0, nullable=False)
    shares = Column(Integer, default=0, nullable=False)
    avg_view_duration = Column(Float, default=0.0, nullable=False)  # seconds
    retention_rate = Column(Float, default=0.0, nullable=False)  # percentage 0-100
    subscribers_gained = Column(Integer, default=0, nullable=False)
    fetched_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="analytics")

    def __repr__(self) -> str:
        return f"<VideoAnalytics(id={self.id}, project_id={self.project_id}, views={self.views})>"


class GenerationHistory(Base):
    """Tracks AI generation steps for cost/performance monitoring."""
    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    step = Column(String(200), nullable=False, index=True)  # e.g. "story_generation", "image_generation", "tts"
    provider = Column(String(200), nullable=False)  # e.g. "ollama", "comfyui", "edge_tts"
    model = Column(String(200), nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="generation_history")

    def __repr__(self) -> str:
        return f"<GenerationHistory(id={self.id}, step='{self.step}', provider='{self.provider}')>"
