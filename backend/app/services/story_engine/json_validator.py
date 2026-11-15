"""
StoryForge AI - Story JSON Validator

Validates, sanitizes, and normalizes AI-generated story payloads.
Ensures strict conformity to required production storytelling schemas.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class StoryValidationError(Exception):
    """Raised when generated story JSON fails validation or structural requirements."""
    pass


def extract_json_from_text(raw_text: str) -> dict[str, Any] | list[Any]:
    """Extract and parse a JSON object or array from potentially messy LLM responses.
    
    Handles markdown codeblocks (```json ... ```), preamble, and postamble text.
    """
    if not raw_text or not raw_text.strip():
        raise StoryValidationError("Received empty response from language model.")

    clean_text = raw_text.strip()

    # 1. Strip markdown fences if present
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
    if code_block_match:
        clean_text = code_block_match.group(1).strip()

    # 2. Try direct parsing
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # 3. Locate innermost/outermost JSON braces
    start_obj = clean_text.find("{")
    end_obj = clean_text.rfind("}")
    start_arr = clean_text.find("[")
    end_arr = clean_text.rfind("]")

    if start_obj != -1 and end_obj != -1 and (start_arr == -1 or start_obj < start_arr):
        candidate = clean_text[start_obj : end_obj + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise StoryValidationError(f"Malformed JSON object detected: {exc}") from exc

    if start_arr != -1 and end_arr != -1:
        candidate = clean_text[start_arr : end_arr + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise StoryValidationError(f"Malformed JSON array detected: {exc}") from exc

    raise StoryValidationError("No parseable JSON structure detected in model output.")


def validate_story(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a parsed story dictionary against the StoryForge AI schema.
    
    Normalizes missing fields with sensible defaults where permissible.
    """
    if not isinstance(data, dict):
        raise StoryValidationError(f"Expected JSON object, got {type(data).__name__}")

    # Required top-level keys
    title = str(data.get("title", "")).strip()
    if not title:
        data["title"] = "Untitled Inspirational Story"

    hook = str(data.get("hook", "")).strip()
    if not hook:
        # Fall back to first scene narration or first sentence
        scenes_preview = data.get("scenes", [])
        if scenes_preview and isinstance(scenes_preview[0], dict):
            hook = scenes_preview[0].get("narration", "A story that will change your perspective.")
        else:
            hook = "A story that will change your perspective."
        data["hook"] = hook

    story = str(data.get("story", "")).strip()
    if not story:
        # Reconstruct story from scenes if available
        scenes = data.get("scenes", [])
        if scenes and isinstance(scenes, list):
            story = " ".join(s.get("narration", "") for s in scenes if isinstance(s, dict))
        data["story"] = story or "Every great journey starts with a single step."

    moral = str(data.get("moral", "")).strip()
    if not moral:
        data["moral"] = "Resilience and faith can overcome life's greatest adversities."

    # Estimated duration normalization
    try:
        data["estimated_duration"] = float(data.get("estimated_duration", 60.0))
    except (ValueError, TypeError):
        data["estimated_duration"] = 60.0

    # Validate scenes
    raw_scenes = data.get("scenes")
    if not raw_scenes or not isinstance(raw_scenes, list):
        raise StoryValidationError("Story must contain a 'scenes' list with at least one scene.")

    validated_scenes: list[dict[str, Any]] = []
    total_scene_duration = 0.0

    for idx, sc in enumerate(raw_scenes, start=1):
        if not isinstance(sc, dict):
            continue

        scene_num = int(sc.get("scene_number", idx))
        narration = str(sc.get("narration", "")).strip()
        if not narration:
            narration = f"Scene {scene_num} unfolds."

        emotion = str(sc.get("emotion", "reflective")).strip()
        visual_prompt = str(sc.get("visual_prompt", "")).strip()
        if not visual_prompt:
            visual_prompt = f"Cinematic scene portraying {emotion}, dramatic lighting, vertical 9:16 framing, photorealistic"

        camera_movement = str(sc.get("camera_movement", "slow_zoom_in")).strip().lower()
        if camera_movement not in {"slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "static"}:
            camera_movement = "slow_zoom_in"

        try:
            dur = float(sc.get("duration", 5.0))
        except (ValueError, TypeError):
            dur = 5.0
        dur = max(2.0, min(30.0, dur))
        total_scene_duration += dur

        music_mood = str(sc.get("music_mood", "Inspirational")).strip().capitalize()

        validated_scenes.append({
            "scene_number": scene_num,
            "narration": narration,
            "emotion": emotion,
            "visual_prompt": visual_prompt,
            "camera_movement": camera_movement,
            "duration": dur,
            "music_mood": music_mood,
        })

    if not validated_scenes:
        raise StoryValidationError("No valid scenes could be parsed from the story payload.")

    data["scenes"] = validated_scenes
    data["total_scene_duration"] = round(total_scene_duration, 1)

    # Validate characters if present
    characters = data.get("characters", [])
    valid_characters: list[dict[str, Any]] = []
    if isinstance(characters, list):
        for ch in characters:
            if isinstance(ch, dict) and ch.get("name"):
                valid_characters.append({
                    "name": str(ch.get("name", "Protagonist")).strip(),
                    "role": str(ch.get("role", "Protagonist")).strip(),
                    "visual_description": str(ch.get("visual_description", "")).strip(),
                    "costume": str(ch.get("costume", "")).strip(),
                })
    data["characters"] = valid_characters

    # Validate or construct persistent CharacterDNA
    char_dna = data.get("character_dna")
    if isinstance(char_dna, dict) and char_dna.get("name"):
        phys = str(char_dna.get("physiological_traits", "")).strip()
        wardrobe = str(char_dna.get("signature_wardrobe", "")).strip()
        lighting = str(char_dna.get("lighting_profile", "Dramatic chiaroscuro with soft rim lighting")).strip()
        name = str(char_dna.get("name", "Protagonist")).strip()
        anchor = str(char_dna.get("anchor_descriptor", "")).strip()
        if not anchor:
            anchor = f"{name}, {phys}, wearing {wardrobe}"
        data["character_dna"] = {
            "name": name,
            "role": str(char_dna.get("role", "Protagonist")).strip(),
            "physiological_traits": phys,
            "signature_wardrobe": wardrobe,
            "lighting_profile": lighting,
            "anchor_descriptor": anchor,
        }
    elif valid_characters:
        c0 = valid_characters[0]
        name = c0["name"]
        desc = c0["visual_description"]
        costume = c0["costume"]
        data["character_dna"] = {
            "name": name,
            "role": c0["role"],
            "physiological_traits": desc,
            "signature_wardrobe": costume,
            "lighting_profile": "Dramatic chiaroscuro with soft rim lighting",
            "anchor_descriptor": f"{name}, {desc}, wearing {costume}",
        }
    else:
        data["character_dna"] = {
            "name": "Protagonist",
            "role": "Protagonist",
            "physiological_traits": "Weathered expressive face, intense grounded eyes",
            "signature_wardrobe": "Dark vintage textured jacket, utilitarian attire",
            "lighting_profile": "Dramatic chiaroscuro with soft rim lighting",
            "anchor_descriptor": "Protagonist with weathered expressive face, intense grounded eyes, dark textured jacket",
        }

    # Optional Comment-Bait debate question for retention
    comment_bait = str(data.get("comment_bait_question", "")).strip()
    if not comment_bait:
        comment_bait = "What would you have done in this exact situation? Let us know below."
    data["comment_bait_question"] = comment_bait

    return data
