"""
StoryForge AI - Visual Continuity Engine

Monitors and enforces continuity across consecutive scene cuts:
- Validates clothing consistency, props, time of day, and environmental weather
- Detects arbitrary prop or setting mutations between adjacent scenes
- Injects continuity bridges into image prompts before generation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContinuityEngine:
    """Validates and enforces visual continuity between consecutive storyboard scenes."""

    def validate_scene_continuity(
        self,
        current_scene: Dict[str, Any],
        previous_scene: Optional[Dict[str, Any]] = None,
        next_scene: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Audit continuity between current scene and its neighbors."""
        report = {
            "is_continuous": True,
            "detected_shifts": [],
            "continuity_injections": [],
        }

        if not previous_scene:
            return report

        # 1. Environment and Time of Day Check
        prev_env = previous_scene.get("environment", "").lower()
        curr_env = current_scene.get("environment", "").lower()

        # Check weather consistency (e.g. rain established in scene 1)
        weather_cues = ["rain", "snow", "fog", "storm", "night", "twilight", "dawn", "midday"]
        for cue in weather_cues:
            if cue in prev_env and cue not in curr_env:
                report["detected_shifts"].append(f"Weather/Atmosphere '{cue}' present in previous scene but missing in current scene")
                report["continuity_injections"].append(f"maintaining continuous {cue} atmosphere")
                report["is_continuous"] = False

        # 2. Key Object / Prop Continuity
        prev_props = set(previous_scene.get("important_objects", []))
        curr_props = set(current_scene.get("important_objects", []))
        shared_props = prev_props.intersection(curr_props)
        for prop in shared_props:
            report["continuity_injections"].append(f"persisting established appearance of {prop}")

        # 3. Character Attire Continuity
        prev_prompt = previous_scene.get("visual_prompt", "").lower()
        curr_prompt = current_scene.get("visual_prompt", "").lower()

        # If previous scene mentions a specific signature wardrobe item, preserve it
        wardrobe_cues = ["jacket", "waistcoat", "coat", "hoodie", "shirt", "dress", "uniform"]
        for item in wardrobe_cues:
            if item in prev_prompt and item not in curr_prompt:
                # Retain wardrobe item
                report["continuity_injections"].append(f"wearing the same {item} established in preceding scene")

        return report

    def enrich_prompt_with_continuity(
        self,
        base_prompt: str,
        current_scene: Dict[str, Any],
        previous_scene: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Inject continuity anchors into prompt when continuous narrative is detected."""
        if not previous_scene:
            return base_prompt

        audit = self.validate_scene_continuity(current_scene, previous_scene)
        if audit["continuity_injections"]:
            injections_str = ", ".join(audit["continuity_injections"])
            return f"{base_prompt}, continuity: {injections_str}"

        return base_prompt
