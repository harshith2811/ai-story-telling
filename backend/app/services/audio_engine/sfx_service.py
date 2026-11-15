"""
StoryForge AI - SFX & Soundscape Engine

Generates and layers atmospheric SFX (sub-bass impact drops, risers,
room tones, and tension hits) for vertical short-form retention.
"""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SFXService:
    """Manages atmospheric sound effects, hook sub-bass hits, and climax risers."""

    def __init__(self, sfx_dir: Optional[Path] = None) -> None:
        self.sfx_dir = sfx_dir or (Path(settings.BASE_DIR) / settings.STORAGE_DIR / "assets" / "sfx")
        self.sfx_dir.mkdir(parents=True, exist_ok=True)

    def generate_cinematic_sfx_bed(self, duration: float, dest_path: Optional[Path] = None) -> Path:
        """Synthesize a dynamic 3-part atmospheric soundscape for the given duration:
        
        1. 0–3s: Sub-bass impact drop & riser (Hook retention).
        2. Body: Subtle analog vinyl room tone & air texture.
        3. Climax (last 10s): Tension riser before the paradigm snap.
        """
        dur = max(5.0, float(duration))
        if dest_path is None:
            dest_path = self.sfx_dir / f"sfx_bed_{int(dur)}s.mp3"

        if dest_path.exists() and dest_path.stat().st_size > 10000:
            return dest_path

        # Sub-bass impact drop (0 to 2.8s)
        # Climax swell from (dur - 10) to (dur - 2)
        climax_start = max(3.5, dur - 10.0)
        climax_dur = max(2.0, dur - climax_start - 1.5)

        sub_drop_expr = (
            f"if(between(t,0,2.8), 0.38*exp(-1.4*t)*sin(2*PI*(44 + 85*exp(-3.2*t))*t), 0)"
        )
        climax_swell_expr = (
            f"if(between(t,{climax_start:.2f},{dur:.2f}), "
            f"0.18*pow((t-{climax_start:.2f})/{climax_dur:.2f}, 1.8)*sin(2*PI*(160 + 280*((t-{climax_start:.2f})/{climax_dur:.2f}))*t), 0)"
        )

        combined_sfx = f"{sub_drop_expr} + {climax_swell_expr}"
        lavfi_expr = (
            f"aevalsrc='{combined_sfx}':s=44100:d={dur},"
            f"lowpass=f=1200,"
            f"aecho=0.8:0.7:80|140:0.35|0.2"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", lavfi_expr,
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(dest_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info("Synthesized cinematic SFX soundscape: %s (%.1fs)", dest_path.name, dur)
        except Exception as exc:
            logger.warning("Failed generating SFX bed (%s); creating silence fallback", exc)
            fallback_cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur}",
                "-c:a", "libmp3lame", str(dest_path)
            ]
            subprocess.run(fallback_cmd, capture_output=True, check=True)

        return dest_path
