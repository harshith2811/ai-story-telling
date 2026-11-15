"""
StoryForge AI - Video Render Pipeline API Router
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import async_session_factory, get_db
from app.models.project import Project, ProjectStatus, RenderStatus, Scene, VideoRender
from app.schemas.project import VideoRenderRequest, VideoRenderResponse
from app.services.image_engine import ImageService
from app.services.music_engine import MusicService
from app.services.subtitle_engine import SubtitleService
from app.services.video_engine import VideoService
from app.services.voice_engine import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory progress tracking for active renders
RENDER_PROGRESS: dict[int, dict[str, Any]] = {}


async def _run_full_render_job(project_id: int, render_id: int) -> None:
    """Asynchronous background rendering pipeline."""
    async with async_session_factory() as db:
        try:
            RENDER_PROGRESS[project_id] = {"progress": 2.0, "status": "initializing", "message": "Starting pipeline..."}

            # Fetch project & scenes
            proj_stmt = select(Project).where(Project.id == project_id)
            proj_res = await db.execute(proj_stmt)
            project = proj_res.scalar_one_or_none()

            render_stmt = select(VideoRender).where(VideoRender.id == render_id)
            render_res = await db.execute(render_stmt)
            render_obj = render_res.scalar_one_or_none()

            if not project or not render_obj:
                logger.error("Project or render job not found: proj=%s render=%s", project_id, render_id)
                return

            render_obj.status = RenderStatus.PROCESSING
            render_obj.started_at = datetime.utcnow()
            project.status = ProjectStatus.RENDERING
            await db.commit()

            scenes_stmt = select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_number)
            scenes_res = await db.execute(scenes_stmt)
            scenes = scenes_res.scalars().all()

            if not scenes:
                raise ValueError("Cannot render video: Project contains no scenes.")

            # 1. Ensure all scene images are generated
            RENDER_PROGRESS[project_id] = {"progress": 10.0, "status": "images", "message": "Synthesizing scene visuals..."}
            image_service = ImageService()
            for sc in scenes:
                if not sc.image_path or not Path(sc.image_path).exists():
                    img_path = await image_service.generate_scene_image(
                        prompt=sc.visual_prompt or f"Cinematic {sc.emotion or 'Inspirational'} scene",
                        scene_number=sc.scene_number,
                        project_id=project_id,
                        emotion=sc.emotion or "Inspirational",
                    )
                    sc.image_path = str(img_path)

            await db.commit()

            # 2. Ensure all scene audios are synthesized
            RENDER_PROGRESS[project_id] = {"progress": 30.0, "status": "audio", "message": "Generating neural speech narration..."}
            voice_service = VoiceService()
            full_script_parts = []
            for sc in scenes:
                if not sc.audio_path or not Path(sc.audio_path).exists():
                    audio_path, duration = await voice_service.generate_speech(
                        text=sc.narration,
                        language=project.language,
                    )
                    sc.audio_path = str(audio_path)
                    sc.duration = round(duration, 1)
                full_script_parts.append(sc.narration)

            await db.commit()

            # 3. Synchronize subtitles (faster-whisper word-level alignment & ASS generator)
            RENDER_PROGRESS[project_id] = {"progress": 50.0, "status": "subtitles", "message": "Aligning word timestamps and styling captions..."}
            subtitle_service = SubtitleService()
            full_script = " ".join(full_script_parts)
            total_duration = sum(float(sc.duration or 5.0) for sc in scenes)

            first_audio = Path(scenes[0].audio_path) if scenes[0].audio_path else None
            timed_words = subtitle_service.align_audio_with_text(first_audio, full_script, total_duration)

            sub_dir = Path(settings.BASE_DIR) / settings.STORAGE_DIR / "outputs" / "subtitles"
            sub_ass_path = sub_dir / f"subtitles_proj_{project_id}.ass"
            sub_srt_path = sub_dir / f"subtitles_proj_{project_id}.srt"

            subtitle_service.generate_ass_subtitles(timed_words, sub_ass_path)
            subtitle_service.generate_srt_subtitles(timed_words, sub_srt_path)

            # 4. Resolve background music
            RENDER_PROGRESS[project_id] = {"progress": 65.0, "status": "music", "message": "Mixing soundtrack & applying audio ducking..."}
            music_service = MusicService()
            primary_mood = scenes[0].music_mood if scenes[0].music_mood else "Inspirational"
            bgm_track = music_service.get_track_for_mood(primary_mood)

            # 5. FFmpeg composition
            def progress_hook(pct: float, msg: str) -> None:
                RENDER_PROGRESS[project_id] = {"progress": round(pct, 1), "status": "rendering", "message": msg}

            video_service = VideoService()
            scenes_data = [
                {
                    "scene_number": s.scene_number,
                    "image_path": s.image_path,
                    "audio_path": s.audio_path,
                    "duration": s.duration or 5.0,
                    "camera_movement": s.camera_movement or "slow_zoom_in",
                }
                for s in scenes
            ]

            output_mp4 = await video_service.render_video_async(
                project_id=project_id,
                scenes=scenes_data,
                music_path=bgm_track,
                music_volume=0.18,
                subtitle_ass_path=sub_ass_path,
                progress_callback=progress_hook,
            )

            # 6. Update database records
            render_obj.status = RenderStatus.COMPLETED
            render_obj.output_path = str(output_mp4)
            render_obj.completed_at = datetime.utcnow()
            project.status = ProjectStatus.COMPLETED
            await db.commit()

            RENDER_PROGRESS[project_id] = {
                "progress": 100.0,
                "status": "completed",
                "message": "Video successfully produced!",
                "output_path": str(output_mp4),
                "download_url": f"/static/outputs/renders/{output_mp4.name}",
            }
            logger.info("Background render pipeline completed for Project #%d", project_id)

        except Exception as exc:
            logger.error("Render failed for project %d: %s", project_id, exc, exc_info=True)
            RENDER_PROGRESS[project_id] = {"progress": 0.0, "status": "failed", "error": str(exc)}
            try:
                render_obj.status = RenderStatus.FAILED
                render_obj.error_message = str(exc)
                project.status = ProjectStatus.FAILED
                await db.commit()
            except Exception:
                pass


@router.post("/start", response_model=VideoRenderResponse)
async def start_render(
    payload: VideoRenderRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger background video assembly and rendering."""
    stmt = select(Project).where(Project.id == payload.project_id)
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    render_job = VideoRender(
        project_id=payload.project_id,
        status=RenderStatus.QUEUED,
        resolution="1080x1920",
        fps=payload.fps or 30,
        format=payload.format or "mp4",
        started_at=datetime.utcnow(),
    )
    db.add(render_job)
    await db.commit()
    await db.refresh(render_job)

    # Dispatch non-blocking background task
    background_tasks.add_task(_run_full_render_job, payload.project_id, render_job.id)

    return render_job


@router.get("/status/{project_id}")
async def get_render_progress(project_id: int) -> Any:
    """Query live rendering progress and status."""
    return RENDER_PROGRESS.get(
        project_id,
        {"progress": 0.0, "status": "idle", "message": "No active render job."}
    )


@router.get("/list/{project_id}", response_model=list[VideoRenderResponse])
async def list_project_renders(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all renders generated for a project."""
    stmt = select(VideoRender).where(VideoRender.project_id == project_id).order_by(desc(VideoRender.started_at))
    res = await db.execute(stmt)
    return res.scalars().all()
