"""GenerationJob ORM model – tracks async AI generation tasks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GenerationJob(Base):
    """Tracks the status and result of an asynchronous generation task."""

    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # story | hooks | storyboard | voice | render
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending | running | completed | failed
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project: Mapped["Project | None"] = relationship(
        "Project", back_populates="generation_jobs"
    )

    def __repr__(self) -> str:
        return f"<GenerationJob id={self.id!r} type={self.job_type!r} status={self.status!r}>"
