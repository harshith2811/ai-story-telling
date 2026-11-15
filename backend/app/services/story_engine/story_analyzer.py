"""
StoryForge AI - Deep Story Understanding & Narrative Analysis Engine

Performs comprehensive narrative decomposition on user stories or generated scripts:
- Extracts Character Bible (protagonists, supporting, antagonists, visual identities)
- Maps Environments, Locations, Timeline & Chronology
- Tracks Critical Props / Important Objects across scenes
- Maps Emotional Progression and Narrative Arc (Beginning, Conflict, Climax, Resolution)
- Formulates Structured Visual Scene Specifications ensuring story fidelity
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from .provider import LLMProvider

logger = logging.getLogger(__name__)

DEEP_STORY_ANALYSIS_SYSTEM_PROMPT = """You are an elite Hollywood Story Analyst, Script Doctor, and Film Director.
Your task is to analyze a complete narrative story and extract a deep, highly structured production blueprint.
Every scene must visually communicate:
1. What is happening (Action).
2. Who is involved (Characters present).
3. Where it is happening (Environment & Location).
4. What the characters are doing (Physical action & body language).
5. What emotions they are experiencing.
6. What objects are important (Props, key items, visual focal points).
7. How the scene connects to the previous and next scenes (Continuity).

NEVER create decorative images unrelated to the actual story. Story accuracy is paramount.

You MUST output ONLY a valid JSON object matching the exact schema provided."""

DEEP_STORY_ANALYSIS_USER_PROMPT = """Analyze this story and produce a complete structured production blueprint:

STORY TITLE: {title}
GENRE / TONE: {genre}
VISUAL STYLE: {visual_style}
TARGET DURATION: {duration} seconds
STORY SCRIPT / TEXT:
\"\"\"
{story_text}
\"\"\"

Return a JSON object with this EXACT structure:
{{
  "story_title": "string",
  "genre": "string",
  "visual_style": "{visual_style}",
  "aspect_ratio": "9:16",
  "narrative_arc": {{
    "beginning": "Summary of setup and inciting incident",
    "conflict": "Summary of escalating tension and obstacle",
    "climax": "Summary of peak emotional revelation or turning point",
    "resolution": "Summary of moral and aftermath"
  }},
  "character_bible": [
    {{
      "character_id": "char_1",
      "name": "Character Name",
      "role": "Protagonist | Supporting | Antagonist",
      "age": "e.g. 65 years old",
      "facial_features": "e.g. deep crow's feet, weathered skin, white beard",
      "hair": "e.g. thinning silver hair",
      "skin": "e.g. olive, sun-weathered",
      "body_type": "e.g. lean, slightly hunched shoulders",
      "clothing": "e.g. worn brown wool tweed jacket over frayed cream shirt",
      "accessories": "e.g. brass jeweler's loupe, tarnished copper ring",
      "visual_identity_description": "Precise 1-2 sentence visual anchor description used across all image generation prompts"
    }}
  ],
  "locations": [
    {{
      "location_id": "loc_1",
      "name": "Location Name",
      "architectural_details": "string",
      "atmosphere_lighting": "string"
    }}
  ],
  "important_objects": [
    {{
      "object_id": "obj_1",
      "name": "Object Name",
      "visual_description": "Exact color, material, wear and condition",
      "story_significance": "Why this object matters"
    }}
  ],
  "scenes": [
    {{
      "scene_id": 1,
      "story_text": "Spoken narration for this exact scene with ellipses (...) for dramatic pauses",
      "visual_description": "Detailed description of the moment",
      "characters_present": ["char_1"],
      "action": "Specific physical action the characters are performing right now",
      "environment": "Exact location and physical setting",
      "emotion": "Dominant emotion experienced by subjects",
      "important_objects": ["obj_1"],
      "camera_angle": "wide_establishing | medium_action | close_up_emotion | extreme_macro_detail | over_the_shoulder",
      "lighting": "Specific lighting physics (e.g. overcast rainy daylight, warm candlelight chiaroscuro)",
      "composition": "Cinematic vertical 9:16 framing notes (e.g. subject in lower third, leading lines)",
      "image_prompt": "Ultra-detailed photography prompt capturing what is happening in this exact moment",
      "negative_prompt": "no static passport headshot, no plain wall, no airbrushed CGI, no text, no watermark",
      "duration": 5.0,
      "continuity_notes": "How this connects to the previous scene (e.g. continues kneeling in rain, holding injured sparrow)"
    }}
  ]
}}

RULES:
1. Divide into 4 to 8 meaningful visual scenes. Do NOT divide by simple word counts. Each scene MUST be an understandable visual beat.
2. Scene durations must total approximately {duration} seconds.
3. Every scene MUST follow the true events of the story.
4. Output ONLY the JSON object. Do not include markdown code blocks or conversational commentary."""


class StoryAnalyzer:
    """Intelligent story comprehension pipeline extracting structured production metadata."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def analyze_story(
        self,
        story_text: str,
        title: Optional[str] = None,
        genre: Optional[str] = "Cinematic Drama",
        visual_style: Optional[str] = "Cinematic realism",
        duration: int = 60,
    ) -> Dict[str, Any]:
        """Analyze a complete story narrative into a structured production blueprint."""
        clean_text = story_text.strip()
        if not clean_text:
            raise ValueError("Story text cannot be empty for analysis")

        derived_title = title or self._extract_working_title(clean_text)

        prompt = DEEP_STORY_ANALYSIS_USER_PROMPT.format(
            title=derived_title,
            genre=genre or "Cinematic Drama",
            visual_style=visual_style or "Cinematic realism",
            duration=duration,
            story_text=clean_text,
        )

        logger.info("Analyzing story narrative '%s' (%d words)...", derived_title, len(clean_text.split()))

        raw_response = await self.provider.generate(
            prompt=prompt,
            system_prompt=DEEP_STORY_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.4,  # Deterministic, high-fidelity structural output
            max_tokens=4000,
        )

        blueprint = self._extract_and_validate_json(raw_response)
        blueprint = self._normalize_blueprint(blueprint, clean_text, derived_title, visual_style, duration)
        return blueprint

    def _extract_working_title(self, text: str) -> str:
        """Derive an appropriate working title from the first sentence or heading."""
        first_line = text.split("\n")[0].strip("# \t\r")
        if len(first_line) > 5 and len(first_line) < 60:
            return first_line
        words = text.split()[:6]
        return " ".join(words).strip(".,!?:;") or "The Untold Story"

    def _extract_and_validate_json(self, raw_text: str) -> Dict[str, Any]:
        """Extract and parse clean JSON from LLM output."""
        text = raw_text.strip()
        # Strip markdown fences if present
        if "```" in text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                text = match.group(1).strip()

        # Find outer braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError("Parsed JSON is not a dictionary")
            return data
        except json.JSONDecodeError as err:
            logger.warning("JSON decode failed: %s; attempting regex repair", err)
            # Basic fallback heuristic repair
            cleaned = re.sub(r",\s*([\]}])", r"\1", text)
            return json.loads(cleaned)

    def _normalize_blueprint(
        self,
        blueprint: Dict[str, Any],
        original_story: str,
        title: str,
        visual_style: str,
        duration: int,
    ) -> Dict[str, Any]:
        """Sanitize, normalize, and complete missing blueprint fields."""
        blueprint.setdefault("story_title", title)
        blueprint.setdefault("genre", "Cinematic")
        blueprint.setdefault("visual_style", visual_style)
        blueprint.setdefault("aspect_ratio", "9:16")
        blueprint.setdefault("raw_story_text", original_story)

        # Ensure Character Bible
        cb = blueprint.get("character_bible", [])
        if not cb or not isinstance(cb, list):
            cb = [
                {
                    "character_id": "char_1",
                    "name": "Protagonist",
                    "role": "Protagonist",
                    "age": "30s",
                    "facial_features": "Expressive eyes, weathered features",
                    "hair": "Dark hair",
                    "skin": "Natural skin tone",
                    "body_type": "Average athletic build",
                    "clothing": "Subdued neutral attire appropriate to setting",
                    "accessories": "Vintage timepiece",
                    "visual_identity_description": "Protagonist, 30s, expressive eyes, dressed in subdued neutral attire",
                }
            ]
        blueprint["character_bible"] = cb

        # Ensure Scenes
        scenes = blueprint.get("scenes", [])
        if not scenes or not isinstance(scenes, list):
            scenes = self._fallback_segmentation(original_story, duration)

        # Normalize scenes and ensure pacing
        normalized_scenes = []
        total_time = 0.0
        for idx, sc in enumerate(scenes, start=1):
            dur = float(sc.get("duration", max(3.0, duration / max(1, len(scenes)))))
            total_time += dur
            normalized_scenes.append(
                {
                    "scene_id": idx,
                    "scene_number": idx,
                    "story_text": sc.get("story_text") or sc.get("narration", f"Scene {idx}"),
                    "narration": sc.get("story_text") or sc.get("narration", f"Scene {idx}"),
                    "visual_description": sc.get("visual_description", ""),
                    "characters_present": sc.get("characters_present", ["char_1"]),
                    "action": sc.get("action", "Observing the unfolding situation"),
                    "environment": sc.get("environment", "Cinematic environment"),
                    "emotion": sc.get("emotion", "Suspense"),
                    "important_objects": sc.get("important_objects", []),
                    "camera_angle": sc.get("camera_angle", "medium_action"),
                    "camera_movement": self._map_camera_movement(sc.get("camera_angle", "medium_action")),
                    "lighting": sc.get("lighting", "Dramatic directional chiaroscuro lighting"),
                    "composition": sc.get("composition", "Vertical 9:16 framing, leading lines to subject"),
                    "image_prompt": sc.get("image_prompt") or sc.get("visual_prompt", ""),
                    "visual_prompt": sc.get("image_prompt") or sc.get("visual_prompt", ""),
                    "negative_prompt": sc.get(
                        "negative_prompt",
                        "no static passport headshot, no plain wall, no smooth airbrushed CGI skin, no watermark, no text",
                    ),
                    "duration": round(dur, 2),
                    "continuity_notes": sc.get("continuity_notes", ""),
                }
            )

        blueprint["scenes"] = normalized_scenes
        blueprint["total_duration"] = round(total_time, 2)
        return blueprint

    def _map_camera_movement(self, camera_angle: str) -> str:
        """Map camera angles to natural Ken Burns movements."""
        ang = camera_angle.lower()
        if "close" in ang or "macro" in ang:
            return "slow_zoom_in"
        if "wide" in ang or "establishing" in ang:
            return "pan_right"
        if "over_the_shoulder" in ang or "medium" in ang:
            return "slow_zoom_in"
        return "slow_zoom_in"

    def _fallback_segmentation(self, story_text: str, duration: int) -> List[Dict[str, Any]]:
        """Fallback scene segmentation if LLM output fails."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story_text) if s.strip()]
        if not sentences:
            sentences = [story_text]

        # Group sentences into 4-6 balanced chunks
        target_count = min(6, max(3, len(sentences) // 2 or 3))
        chunk_size = max(1, len(sentences) // target_count)
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunks.append(" ".join(sentences[i : i + chunk_size]))

        scenes = []
        dur_per_scene = max(3.0, duration / max(1, len(chunks)))
        for i, chunk in enumerate(chunks, 1):
            scenes.append(
                {
                    "scene_id": i,
                    "story_text": chunk,
                    "visual_description": f"Visual realization of: {chunk[:80]}...",
                    "characters_present": ["char_1"],
                    "action": "Living through the moment",
                    "environment": "Authentic narrative environment",
                    "emotion": "Reflective",
                    "camera_angle": "wide_establishing" if i == 1 else "medium_action",
                    "lighting": "Natural cinematic lighting",
                    "duration": dur_per_scene,
                }
            )
        return scenes
