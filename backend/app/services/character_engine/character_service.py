"""
StoryForge AI - Character Consistency & Character Bible Engine

Maintains permanent Character Bibles across multi-scene video productions:
- Tracks Character IDs, Names, Ages, Facial Features, Hair, Skin, Body Types,
  Signature Clothing, Accessories, and Visual Identity Descriptors
- Preserves multi-character identity across all scene cuts
- Supports reference image conditioning metadata and persistent character sheets
- Enforces strict visual continuity without relying on random seeds
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class CharacterService:
    """Manages permanent character bibles, visual consistency anchors, and reference sheets."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = storage_dir or (Path(settings.BASE_DIR) / settings.STORAGE_DIR / "characters")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def build_character_bible(self, story_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract or build a comprehensive Character Bible from story metadata."""
        # 1. Prefer explicit character_bible from deep story analysis
        if "character_bible" in story_data and isinstance(story_data["character_bible"], list) and story_data["character_bible"]:
            bible = [self._normalize_bible_entry(c, idx) for idx, c in enumerate(story_data["character_bible"], start=1)]
            return bible

        # 2. Check for legacy character_dna
        if "character_dna" in story_data and isinstance(story_data["character_dna"], dict):
            dna = story_data["character_dna"]
            return [self._normalize_dna_profile(dna)]

        # 3. Check for standard characters list
        characters = story_data.get("characters", [])
        if characters and isinstance(characters, list) and len(characters) > 0:
            return [self._normalize_bible_entry(c, idx) for idx, c in enumerate(characters, start=1)]

        # 4. Fallback default protagonist
        return [self._create_default_character(story_data)]

    def _normalize_bible_entry(self, char: Dict[str, Any], index: int = 1) -> Dict[str, Any]:
        """Normalize a dictionary entry into a full 11-attribute Character Bible record."""
        char_id = str(char.get("character_id") or f"char_{index}").strip()
        name = str(char.get("name", f"Character {index}")).strip()
        role = str(char.get("role", "Protagonist" if index == 1 else "Supporting")).strip()
        age = str(char.get("age", "35 years old")).strip()
        face = str(char.get("facial_features", "Expressive, determined features")).strip()
        hair = str(char.get("hair", "Dark natural hair")).strip()
        skin = str(char.get("skin", "Natural skin tone with visible skin texture")).strip()
        body = str(char.get("body_type", "Medium build, grounded posture")).strip()
        clothing = str(char.get("clothing", char.get("costume", "Signature neutral attire"))).strip()
        accessories = str(char.get("accessories", "None")).strip()
        ref_img = char.get("reference_image_path")

        # Synthesize unambiguous anchor descriptor
        anchor = char.get("visual_identity_description") or char.get("anchor_descriptor")
        if not anchor:
            acc_part = f", with {accessories}" if accessories and accessories.lower() != "none" else ""
            anchor = f"{age} {name}, {face}, {hair}, {body}, wearing {clothing}{acc_part}"

        ref_prompt = (
            f"Cinematic 9:16 vertical character concept sheet of {anchor}. "
            f"Neutral atmospheric studio lighting, visible skin pores, fine fabric textures, 8k resolution."
        )

        return {
            "character_id": char_id,
            "name": name,
            "role": role,
            "age": age,
            "facial_features": face,
            "hair": hair,
            "skin": skin,
            "body_type": body,
            "clothing": clothing,
            "accessories": accessories,
            "visual_identity_description": anchor,
            "anchor_descriptor": anchor,
            "reference_image_path": ref_img,
            "reference_prompt": ref_prompt,
        }

    def _normalize_dna_profile(self, dna: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize legacy CharacterDNA into Character Bible format."""
        name = str(dna.get("name", "Protagonist")).strip()
        role = str(dna.get("role", "Protagonist")).strip()
        phys = str(dna.get("physiological_traits", "")).strip()
        wardrobe = str(dna.get("signature_wardrobe", "")).strip()
        lighting = str(dna.get("lighting_profile", "Dramatic chiaroscuro")).strip()
        anchor = str(dna.get("anchor_descriptor", "")).strip()
        if not anchor:
            anchor = f"{name}, {phys}, wearing {wardrobe}"

        return self._normalize_bible_entry(
            {
                "character_id": "char_1",
                "name": name,
                "role": role,
                "facial_features": phys,
                "clothing": wardrobe,
                "visual_identity_description": anchor,
                "lighting_profile": lighting,
            },
            1,
        )

    def _create_default_character(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default protagonist record tailored to language or story tone."""
        story = story_data.get("story", "")
        is_telugu = any(0x0C00 <= ord(c) <= 0x0C7F for c in story)

        if is_telugu:
            return self._normalize_bible_entry(
                {
                    "character_id": "char_1",
                    "name": "రవి (Ravi)",
                    "role": "Protagonist",
                    "age": "24 years old",
                    "facial_features": "Sharp jawline, deep expressive eyes, calm yet determined gaze",
                    "hair": "Short neat black hair",
                    "skin": "Sun-kissed South Asian skin tone",
                    "body_type": "Lean athletic build",
                    "clothing": "Classic navy blue buttoned shirt with rolled-up sleeves, dark grey trousers",
                    "accessories": "Vintage brass wristwatch",
                },
                1,
            )

        return self._normalize_bible_entry(
            {
                "character_id": "char_1",
                "name": "Alex",
                "role": "Protagonist",
                "age": "28 years old",
                "facial_features": "Focused brow, resolute chin, subtle scar near left eyebrow",
                "hair": "Short textured dark brown hair",
                "skin": "Fair weather-exposed skin",
                "body_type": "Athletic build",
                "clothing": "Charcoal grey tactical utility jacket over dark crewneck tee",
                "accessories": "Leather-banded wrist compass",
            },
            1,
        )

    def extract_characters_from_story(self, story_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convenience alias returning normalized character list."""
        return self.build_character_bible(story_data)

    def save_character_bible(self, project_id: int, bible: List[Dict[str, Any]]) -> Path:
        """Persist character bible for a project to disk."""
        target_file = self.storage_dir / f"project_{project_id}_bible.json"
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(bible, f, indent=2, ensure_ascii=False)
        logger.info("Saved Character Bible with %d characters to %s", len(bible), target_file)
        return target_file

    def load_character_bible(self, project_id: int) -> Optional[List[Dict[str, Any]]]:
        """Load character bible from disk if present."""
        target_file = self.storage_dir / f"project_{project_id}_bible.json"
        if target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load character bible from %s: %s", target_file, e)
        return None

    def inject_character_consistency_into_prompt(
        self, base_visual_prompt: str, character_profile: dict[str, Any]
    ) -> str:
        """Inject strict character anchor keywords into a scene's visual prompt."""
        name = character_profile.get("name", "the protagonist")
        desc = character_profile.get("visual_description", "")
        costume = character_profile.get("costume") or character_profile.get("clothing", "")

        consistency_anchor = f"featuring {name} ({desc}, dressed in {costume})"

        if name.lower() not in base_visual_prompt.lower():
            enhanced = f"{base_visual_prompt}, {consistency_anchor}, consistent character likeness, 9:16 aspect ratio"
        else:
            enhanced = f"{base_visual_prompt}, dressed in {costume}, consistent character likeness, 9:16 aspect ratio"

        return f"{enhanced}, no watermarks, no unwanted text, cinematic color grade"

    def inject_character_dna_into_scenes(
        self, scenes: List[Dict[str, Any]], character_dna_or_bible: Any
    ) -> List[Dict[str, Any]]:
        """Inject consistent character anchors into scene visual prompts based on character presence."""
        if isinstance(character_dna_or_bible, dict):
            bible = [self._normalize_dna_profile(character_dna_or_bible)]
        elif isinstance(character_dna_or_bible, list):
            bible = character_dna_or_bible
        else:
            return scenes

        # Create quick lookup by character_id and name
        char_map: Dict[str, Dict[str, Any]] = {}
        for c in bible:
            char_map[c.get("character_id", "").lower()] = c
            char_map[c.get("name", "").lower()] = c

        primary_char = bible[0] if bible else None

        for sc in scenes:
            prompt = sc.get("visual_prompt", "").strip()
            prompt_lower = prompt.lower()

            # Preserve pure environmental, landscape, or technical shots
            is_environmental = any(
                term in prompt_lower
                for term in [
                    "space shot", "celestial", "asteroid", "satellite", "radar monitor", "macro close-up",
                    "wide aerial", "landscape", "vault door", "skyline", "telescope array", "streetlamp",
                    "cobblestones", "laboratory desk", "workbench"
                ]
            ) and not any(
                k in prompt_lower
                for k in ["dr.", "character", "protagonist", "person", "eyes of", "man", "woman", "kneeling", "holding"]
            )

            if is_environmental:
                continue

            # Identify which characters are present in this scene
            present_chars = []
            declared_present = sc.get("characters_present", [])
            for ref in declared_present:
                if str(ref).lower() in char_map:
                    present_chars.append(char_map[str(ref).lower()])

            if not present_chars and primary_char:
                # Default to primary character if scene appears to involve human action
                if any(k in prompt_lower for k in ["man", "woman", "person", "protagonist", "he", "she", "character", "hands"]):
                    present_chars = [primary_char]

            if present_chars:
                # Build combined multi-character anchor
                anchors_text = "; ".join(
                    f"{c.get('name')} ({c.get('visual_identity_description')})" for c in present_chars
                )
                if not any(c.get("name", "").lower() in prompt_lower for c in present_chars):
                    sc["visual_prompt"] = (
                        f"{prompt}, featuring {anchors_text} in dynamic environmental action, "
                        f"cinematic situational framing, ARRI Alexa 65 cinematography"
                    )

        return scenes
