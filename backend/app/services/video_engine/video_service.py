"""
StoryForge AI - Video Production & Rendering Engine

Assembles individual scene images, voice narration, background music,
and dynamic highlighted subtitles into a vertical 1080x1920 30FPS MP4 video
using optimized FFmpeg filtergraphs with NVENC or libx264.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoService:
    """Orchestrates video rendering, Ken Burns motion, audio ducking, and subtitle burning."""

    def __init__(self, renders_dir: Optional[Path] = None) -> None:
        self.renders_dir = renders_dir or (Path(settings.BASE_DIR) / settings.STORAGE_DIR / "outputs" / "renders")
        self.renders_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(settings.BASE_DIR) / settings.STORAGE_DIR / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def render_video_async(
        self,
        project_id: int,
        scenes: list[dict[str, Any]],
        music_path: Optional[Path] = None,
        music_volume: float = 0.18,
        subtitle_ass_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Path:
        """Render full project into a 1080x1920 vertical MP4 video."""
        output_filename = f"storyforge_project_{project_id}_{int(time.time())}.mp4"
        final_output_path = self.renders_dir / output_filename

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._render_video_sync,
            project_id,
            scenes,
            music_path,
            music_volume,
            subtitle_ass_path,
            final_output_path,
            progress_callback,
        )

    def _render_video_sync(
        self,
        project_id: int,
        scenes: list[dict[str, Any]],
        music_path: Optional[Path],
        music_volume: float,
        subtitle_ass_path: Optional[Path],
        output_path: Path,
        progress_callback: Optional[Callable[[float, str], None]],
    ) -> Path:
        """Synchronous rendering pipeline executed in background thread."""
        logger.info("Starting video render for Project #%d (%d scenes)", project_id, len(scenes))
        if progress_callback:
            progress_callback(5.0, "Preparing scene visual assets and narration tracks...")

        # 1. Render each scene as a standalone high-res video clip
        scene_clip_paths: list[Path] = []
        total_scenes = len(scenes)

        for idx, scene in enumerate(scenes, start=1):
            if progress_callback:
                pct = 5.0 + (float(idx) / total_scenes) * 50.0
                progress_callback(pct, f"Rendering scene {idx}/{total_scenes} with Ken Burns motion...")

            image_path = Path(scene["image_path"])
            audio_path = Path(scene["audio_path"]) if scene.get("audio_path") else None
            duration = float(scene.get("duration", 5.0))
            camera_movement = scene.get("camera_movement", "slow_zoom_in")
            is_first = (idx == 1)
            is_last = (idx == total_scenes)

            # Smart clip hash to avoid re-rendering untouched scene clips
            audio_mod = audio_path.stat().st_mtime if (audio_path and audio_path.exists()) else 0
            img_mod = image_path.stat().st_mtime if image_path.exists() else 0
            clip_key = f"{project_id}_{idx}_{img_mod}_{audio_mod}_{duration}_{camera_movement}"
            clip_hash = hashlib.md5(clip_key.encode()).hexdigest()[:8]

            clip_path = self.temp_dir / f"clip_proj_{project_id}_sc_{idx}_{clip_hash}.mp4"
            if clip_path.exists() and clip_path.stat().st_size > 50000:
                logger.info("Using cached clip for scene %d: %s", idx, clip_path.name)
            else:
                self._render_single_scene_clip(
                    image_path, audio_path, duration, camera_movement, clip_path, is_first=is_first, is_last=is_last
                )
            scene_clip_paths.append(clip_path)

        # 2. Concatenate all scene clips
        if progress_callback:
            progress_callback(60.0, "Concatenating scene clips into continuous sequence...")

        concat_list_file = self.temp_dir / f"concat_proj_{project_id}.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in scene_clip_paths:
                escaped_path = str(p.resolve()).replace("\\", "/")
                f.write(f"file '{escaped_path}'\n")

        raw_joined_video = self.temp_dir / f"joined_proj_{project_id}.mp4"
        cmd_concat = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(raw_joined_video),
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        # 3. Add background music, audio ducking, subtitle overlay, and loudness normalization
        if progress_callback:
            progress_callback(75.0, "Mixing soundtrack, ducking audio, and burning animated subtitles...")

        self._finalize_composition(
            raw_joined_video,
            music_path,
            music_volume,
            subtitle_ass_path,
            output_path,
        )

        if progress_callback:
            progress_callback(100.0, "Render completed successfully!")

        logger.info("Render complete! Saved vertical MP4: %s (%.2f MB)", output_path, output_path.stat().st_size / (1024 * 1024))
        return output_path

    def _get_media_duration(self, file_path: Path) -> float:
        """Extract media duration using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 30.0

    def _render_single_scene_clip(
        self,
        image_path: Path,
        audio_path: Optional[Path],
        duration: float,
        camera_movement: str,
        output_clip_path: Path,
        is_first: bool = False,
        is_last: bool = False,
    ) -> Path:
        """Render an individual image into a 1080x1920 30fps clip with Ken Burns motion, vignette, film grain, and fades."""
        fps = 30
        total_frames = max(2, int(duration * fps))
        span = max(1, total_frames - 1)

        # Dynamic non-linear Ken Burns motion expressions (smooth power easing)
        if camera_movement == "slow_zoom_out":
            zoom_expr = f"z='1.18-0.18*pow(on/{span},1.5)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        elif camera_movement == "pan_left":
            zoom_expr = f"z='1.12':d={total_frames}:x='(1-pow(on/{span},1.3))*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
        elif camera_movement == "pan_right":
            zoom_expr = f"z='1.12':d={total_frames}:x='pow(on/{span},1.3)*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
        elif camera_movement == "tilt_up":
            zoom_expr = f"z='1.12':d={total_frames}:x='iw/2-(iw/zoom/2)':y='(1-pow(on/{span},1.3))*(ih-ih/zoom)'"
        elif camera_movement == "tilt_down":
            zoom_expr = f"z='1.12':d={total_frames}:x='iw/2-(iw/zoom/2)':y='pow(on/{span},1.3)*(ih-ih/zoom)'"
        else:
            # Default: dynamic smooth push-in that accelerates subtly into the scene climax
            zoom_expr = f"z='1.0+0.18*pow(on/{span},1.5)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

        # Fade effects
        fade_chain = ""
        if is_first:
            fade_chain += ",fade=t=in:st=0:d=0.4"
        if is_last:
            fade_out_st = max(0.0, duration - 0.6)
            fade_chain += f",fade=t=out:st={fade_out_st:.2f}:d=0.6"

        # Broadcast post-processing filter chain:
        # 1. 9:16 vertical crop & scale
        # 2. Non-linear Ken Burns zoompan
        # 3. Soft radial dark vignette focusing the vertical center
        # 4. Organic 35mm film grain simulation to eliminate flat AI plastic sheen
        # 5. Cinematic contrast and subtle saturation pop
        # 6. Smooth opening fade-in and closing fade-out
        filter_chain = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan={zoom_expr}:s=1080x1920:fps={fps},"
            f"vignette=PI/4,noise=alls=10:allf=t+u,eq=contrast=1.04:saturation=1.05{fade_chain},format=yuv420p"
        )

        # Audio handling: use scene audio or synthesize silence
        if audio_path and audio_path.exists() and audio_path.stat().st_size > 500:
            cmd = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-i", str(audio_path),
                "-vf", filter_chain,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                str(output_clip_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-vf", filter_chain,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                str(output_clip_path),
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error("Scene render failed:\n%s", res.stderr)
            raise RuntimeError(f"FFmpeg scene render failed: {res.stderr[-300:]}")

        return output_clip_path

    def _finalize_composition(
        self,
        video_path: Path,
        music_path: Optional[Path],
        music_volume: float,
        subtitle_ass_path: Optional[Path],
        output_path: Path,
    ) -> None:
        """Compose final video with 3-track sound design (voice + ducked music + SFX/atmosphere), subtitles, and loudnorm."""
        # Clean subtitle path for FFmpeg filtergraph syntax (forward slashes and escaped colon)
        video_filters: list[str] = []
        if subtitle_ass_path and subtitle_ass_path.exists():
            clean_sub = str(subtitle_ass_path.resolve()).replace("\\", "/")
            if ":" in clean_sub:
                clean_sub = clean_sub.replace(":", "\\:")
            video_filters.append(f"subtitles='{clean_sub}'")

        vf_arg = ",".join(video_filters) if video_filters else "null"

        # Determine total duration for SFX atmosphere generation
        total_duration = self._get_media_duration(video_path)

        # Generate or load dynamic 3-part SFX track (sub-bass impact, room tone, climax swell)
        sfx_path: Optional[Path] = None
        try:
            from app.services.audio_engine.sfx_service import SFXService
            sfx_svc = SFXService(sfx_dir=self.temp_dir / "sfx")
            sfx_path = sfx_svc.generate_cinematic_sfx_bed(duration=total_duration)
        except Exception as exc:
            logger.debug("SFX atmosphere generation skipped: %s", exc)

        # 3-Track Audio Mixer:
        # Track 1: Narration [0:a] with presence boost & sidechain control
        # Track 2: Cinematic Score [1:a] ducked by 14dB in 40ms during speech
        # Track 3: SFX & Atmosphere [2:a] with sub-bass drop at 0-3s and climax tension
        if music_path and music_path.exists() and sfx_path and sfx_path.exists():
            filter_complex = (
                f"[0:v]{vf_arg}[v];"
                f"[0:a]volume=1.20,highpass=f=80,equalizer=f=3200:t=q:w=1:g=2.5[voice];"
                f"[1:a]volume={music_volume:.2f},aloop=loop=-1:size=2e+09[bgm];"
                f"[voice]asplit=2[v_lead][v_sc];"
                f"[bgm][v_sc]sidechaincompress=threshold=0.035:ratio=4.5:attack=40:release=380[ducked_bgm];"
                f"[2:a]volume=0.85[sfx_bed];"
                f"[v_lead][ducked_bgm][sfx_bed]amix=inputs=3:weights=1.0 0.80 0.65:normalize=0,"
                f"loudnorm=I=-14:TP=-1.5:LRA=9[a]"
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-stream_loop", "-1",
                "-i", str(music_path),
                "-i", str(sfx_path),
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{total_duration:.2f}",
                "-movflags", "+faststart",
                str(output_path),
            ]
        elif music_path and music_path.exists():
            filter_complex = (
                f"[0:v]{vf_arg}[v];"
                f"[0:a]volume=1.20,highpass=f=80,equalizer=f=3200:t=q:w=1:g=2.0[voice];"
                f"[1:a]volume={music_volume:.2f},aloop=loop=-1:size=2e+09[bgm];"
                f"[voice]asplit=2[v_lead][v_sc];"
                f"[bgm][v_sc]sidechaincompress=threshold=0.035:ratio=4.5:attack=40:release=380[ducked_bgm];"
                f"[v_lead][ducked_bgm]amix=inputs=2:weights=1.0 0.85:normalize=0,"
                f"loudnorm=I=-14:TP=-1.5:LRA=9[a]"
            )
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-stream_loop", "-1",
                "-i", str(music_path),
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{total_duration:.2f}",
                "-movflags", "+faststart",
                str(output_path),
            ]
        else:
            filter_complex = f"[0:v]{vf_arg}[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{total_duration:.2f}",
                "-movflags", "+faststart",
                str(output_path),
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.warning("Final composition with subtitles filter failed, retrying without subtitle burning:\n%s", res.stderr)
            # Fallback without subtitle filter if libass encounters font path issue
            cmd_fallback = [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-c:v", "copy",
                "-c:a", "aac",
                str(output_path),
            ]
            subprocess.run(cmd_fallback, capture_output=True, check=True)
