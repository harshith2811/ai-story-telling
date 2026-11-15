"""
StoryForge AI - Storyboard Engine

Orchestrates scene-by-scene storyboard planning, duration alignment,
prompt adjustments, and visual direction for vertical short-form video.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class StoryboardService:
    """Manages scene sequencing, pacing, and storyboard editing."""

    def build_storyboard_from_story(
        self,
        story_data: dict[str, Any],
        character_profiles: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Construct an editable storyboard from validated story scenes."""
        scenes = story_data.get("scenes", [])
        primary_char = character_profiles[0] if (character_profiles and len(character_profiles) > 0) else None

        storyboard_scenes: list[dict[str, Any]] = []

        for idx, sc in enumerate(scenes, start=1):
            narration = sc.get("narration", f"Scene {idx} narration.")
            emotion = sc.get("emotion", "Inspirational")
            base_prompt = sc.get("visual_prompt", f"Cinematic scene portraying {emotion}")
            camera_movement = sc.get("camera_movement", "slow_zoom_in")
            duration = float(sc.get("duration", 5.0))
            music_mood = sc.get("music_mood", "Inspirational")

            # Enrich prompt with vertical cinematography directives
            enriched_prompt = base_prompt
            if "vertical" not in enriched_prompt.lower() and "9:16" not in enriched_prompt:
                enriched_prompt = f"Vertical 9:16 portrait composition, {enriched_prompt}"

            if primary_char and idx in {1, 2, 4}:
                char_name = primary_char.get("name", "protagonist")
                if char_name.lower() not in enriched_prompt.lower():
                    enriched_prompt = f"{enriched_prompt}, featuring {char_name} ({primary_char.get('costume')})"

            storyboard_scenes.append({
                "scene_number": idx,
                "narration": narration,
                "emotion": emotion,
                "visual_prompt": enriched_prompt,
                "camera_movement": camera_movement,
                "duration": duration,
                "music_mood": music_mood,
                "image_path": sc.get("image_path"),
                "audio_path": sc.get("audio_path"),
            })

        return storyboard_scenes

    def adjust_scene_durations(
        self, scenes: list[dict[str, Any]], target_total_duration: float
    ) -> list[dict[str, Any]]:
        """Scale scene durations proportionally to fit target duration perfectly."""
        if not scenes:
            return []

        current_total = sum(float(s.get("duration", 5.0)) for s in scenes)
        if current_total <= 0:
            current_total = len(scenes) * 5.0

        scale_factor = target_total_duration / current_total

        updated = []
        for s in scenes:
            dur = round(float(s.get("duration", 5.0)) * scale_factor, 1)
            dur = max(2.0, min(20.0, dur))
            s_copy = dict(s)
            s_copy["duration"] = dur
            updated.append(s_copy)

        return updated
