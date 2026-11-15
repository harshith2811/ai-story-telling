"""
StoryForge AI - Analytics Schemas

Pydantic models for analytics API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Video Analytics Schemas
# ═══════════════════════════════════════════════════════════════════════════

class VideoAnalyticsCreate(BaseModel):
    """Schema for recording analytics data."""
    project_id: int
    platform: str = "youtube"
    video_id: Optional[str] = None
    views: int = Field(0, ge=0)
    likes: int = Field(0, ge=0)
    comments: int = Field(0, ge=0)
    shares: int = Field(0, ge=0)
    avg_view_duration: float = Field(0.0, ge=0)
    retention_rate: float = Field(0.0, ge=0, le=100)
    subscribers_gained: int = Field(0, ge=0)


class VideoAnalyticsUpdate(BaseModel):
    """Schema for updating analytics data."""
    views: Optional[int] = Field(None, ge=0)
    likes: Optional[int] = Field(None, ge=0)
    comments: Optional[int] = Field(None, ge=0)
    shares: Optional[int] = Field(None, ge=0)
    avg_view_duration: Optional[float] = Field(None, ge=0)
    retention_rate: Optional[float] = Field(None, ge=0, le=100)
    subscribers_gained: Optional[int] = Field(None, ge=0)


class VideoAnalyticsResponse(BaseModel):
    """Schema for analytics API responses."""
    id: int
    project_id: int
    platform: str
    video_id: Optional[str] = None
    views: int
    likes: int
    comments: int
    shares: int
    avg_view_duration: float
    retention_rate: float
    subscribers_gained: int
    fetched_at: datetime

    model_config = {"from_attributes": True}


class VideoAnalyticsList(BaseModel):
    """Schema for listing analytics across projects."""
    items: list[VideoAnalyticsResponse]
    total: int


class AnalyticsSummary(BaseModel):
    """Aggregated analytics summary across all projects."""
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    avg_retention_rate: float = 0.0
    total_subscribers_gained: int = 0
    total_videos: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# Generation History Schemas
# ═══════════════════════════════════════════════════════════════════════════

class GenerationHistoryCreate(BaseModel):
    """Schema for recording a generation step."""
    project_id: int
    step: str = Field(..., min_length=1, max_length=200)
    provider: str = Field(..., min_length=1, max_length=200)
    model: Optional[str] = None
    duration_ms: int = Field(0, ge=0)
    tokens_used: int = Field(0, ge=0)
    error_message: Optional[str] = None


class GenerationHistoryResponse(BaseModel):
    """Schema for generation history API responses."""
    id: int
    project_id: int
    step: str
    provider: str
    model: Optional[str] = None
    duration_ms: int
    tokens_used: int
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerationHistoryList(BaseModel):
    """Schema for listing generation history."""
    items: list[GenerationHistoryResponse]
    total: int
