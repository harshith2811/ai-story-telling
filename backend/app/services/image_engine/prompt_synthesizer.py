"""
StoryForge AI - Scene-to-Image Prompt Synthesizer & Visual Style Registry

Constructs rich, narrative-accurate image generation prompts from deep scene metadata:
- Integrates Character Appearances & Actions
- Integrates Physical Environment, Weather & Lighting Physics
- Integrates Camera Angle, Composition, and Depth of Field
- Applies Visual Style Rules (Cinematic Realism, Pixar 3D, Anime, Watercolor, etc.)
- Injects Visual Continuity from Previous Scenes
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisualStyleRegistry:
    """Registry of comprehensive visual style presets and their optical signatures."""

    STYLES: Dict[str, Dict[str, str]] = {
        "cinematic_realism": {
            "name": "Cinematic Realism",
            "optics": (
                "Shot on ARRI Alexa 65 with 50mm Cooke Anamorphic lens at f/1.4, vertical 9:16 cinematic still, "
                "dramatic chiaroscuro lighting, natural volumetric atmosphere, deep cinematic shadows, "
                "unfiltered 35mm film grain, visible skin pores, natural sweat sheen, fine authentic textures, "
                "Kodak Vision3 500T color grade"
            ),
            "negative": (
                "no static passport headshot, no plain studio wall, no airbrushed smooth plastic CGI skin, "
                "no 3D render sheen, no cartoon, no anime, no oversaturated digital gloss, no watermarks, no text"
            ),
        },
        "pixar_3d": {
            "name": "Pixar-inspired 3D Animation",
            "optics": (
                "High-end 3D animated film render in the style of modern Pixar and Disney feature films, "
                "charming stylized character proportions with deeply expressive eyes, tactile subsurface scattering on skin, "
                "physically-based rendering, rich warm lighting, volumetric dust motes, vibrant emotional color palette, "
                "vertical 9:16 composition, rendered in Octane with raytraced lighting"
            ),
            "negative": (
                "no live action photography, no photorealistic human skin pores, no grimy film grain, "
                "no flat 2D vector, no low-poly, no dull flat lighting, no watermarks, no text"
            ),
        },
        "anime": {
            "name": "Anime & Studio Ghibli",
            "optics": (
                "Masterpiece anime movie still in the distinct visual style of Makoto Shinkai and Studio Ghibli, "
                "breathtaking hand-painted background art, luminous atmospheric lighting, emotional cel-shaded character art, "
                "detailed eyes with delicate light reflections, expressive line art, vibrant skies and golden hour glow, "
                "vertical 9:16 framing, 8k resolution anime keyframe"
            ),
            "negative": (
                "no 3D CGI plastic render, no live-action photograph, no photorealistic skin pores, "
                "no muddy colors, no Western comic style, no watermarks, no subtitles, no text"
            ),
        },
        "watercolor": {
            "name": "Watercolor Fine Art",
            "optics": (
                "Expressive fine art watercolor painting on cold-press textured cotton paper, visible wet-on-wet paint washes, "
                "delicate ink contour outlines, organic pigment pooling and blooming, soft bleeding edges, "
                "luminous paper whites shining through translucent glazes, poetic atmospheric storytelling, vertical 9:16"
            ),
            "negative": (
                "no photograph, no sharp digital 3D CGI, no glossy plastic, no harsh computer rendering, "
                "no vector flat art, no watermarks, no text"
            ),
        },
        "storybook": {
            "name": "Storybook Illustration",
            "optics": (
                "Charming vintage children's book illustration in the style of Beatrix Potter and classic fairy tales, "
                "whimsical storybook aesthetic, gentle gouache and colored pencil textures, warm nostalgic palette, "
                "enchanting fairytale atmosphere, detailed storybook composition, vertical 9:16"
            ),
            "negative": (
                "no photographic realism, no modern 3D CGI, no grimdark horror, no harsh digital lighting, "
                "no watermarks, no text"
            ),
        },
        "documentary": {
            "name": "Documentary Vintage",
            "optics": (
                "Historical documentary archive photograph, authentic Leica M3 35mm photography, natural unposed photojournalism, "
                "candid human emotion, authentic historical patina, subtle monochrome or faded Kodachrome color grading, "
                "tactile vintage grain, real environmental setting, vertical 9:16 composition"
            ),
            "negative": (
                "no staged studio glamour, no modern digital plastic sheen, no airbrushed faces, no cartoon, "
                "no futuristic CGI, no watermarks, no text"
            ),
        },
        "fantasy": {
            "name": "Fantasy Epic",
            "optics": (
                "Epic high fantasy cinematic film still, sweeping mythical atmosphere, magical volumetric rim lighting, "
                "ancient weathered stone and ornate metal textures, otherworldly atmospheric haze, dramatic deep contrast, "
                "blockbuster fantasy movie production design, vertical 9:16 framing, 8k resolution"
            ),
            "negative": (
                "no modern urban elements, no casual contemporary clothing, no plastic CGI, no low-budget render, "
                "no watermarks, no text"
            ),
        },
        "photorealistic": {
            "name": "Hyper-Photorealistic",
            "optics": (
                "Award-winning National Geographic editorial photograph, captured on Hasselblad H6D-100c with 80mm prime lens, "
                "true-to-life optical depth of field, authentic natural ambient lighting, razor-sharp organic micro-textures, "
                "natural skin imperfections and fabric weaves, uncompromising realism, vertical 9:16"
            ),
            "negative": (
                "no CGI, no 3D render, no airbrushing, no digital smoothing, no illustration, no drawing, "
                "no studio portrait backdrop, no watermarks, no text"
            ),
        },
    }

    @classmethod
    def get_style(cls, style_name: Optional[str]) -> Dict[str, str]:
        """Lookup style optics and negative guidance with sensible default."""
        if not style_name:
            return cls.STYLES["cinematic_realism"]

        key = style_name.lower().replace(" ", "_").replace("-", "_")
        for k in cls.STYLES:
            if k in key or key in k:
                return cls.STYLES[k]

        return cls.STYLES["cinematic_realism"]


class ScenePromptSynthesizer:
    """Constructs Hollywood-grade scene-to-image prompts from deep scene metadata."""

    def __init__(self, default_style: str = "cinematic_realism"):
        self.default_style = default_style

    def synthesize_prompt(
        self,
        scene: Dict[str, Any],
        character_bible: Optional[List[Dict[str, Any]]] = None,
        visual_style: Optional[str] = None,
        previous_scene: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, str]:
        """Construct full (positive_prompt, negative_prompt) tuple tailored for image generation models."""
        style_info = VisualStyleRegistry.get_style(visual_style or self.default_style)

        # 1. Base Action & Subject
        action = scene.get("action") or scene.get("visual_description") or scene.get("narration", "")
        environment = scene.get("environment") or "an authentic atmospheric setting"
        emotion = scene.get("emotion") or "intense focus"
        camera_angle = scene.get("camera_angle") or "medium_action"
        lighting = scene.get("lighting") or "dramatic chiaroscuro lighting"

        # 2. Camera framing mapping
        framing_desc = self._map_camera_framing(camera_angle)

        # 3. Resolve Characters present
        char_desc_list = []
        if character_bible:
            char_map = {c.get("character_id", "").lower(): c for c in character_bible}
            char_map.update({c.get("name", "").lower(): c for c in character_bible})

            declared_chars = scene.get("characters_present", [])
            for c_ref in declared_chars:
                c_data = char_map.get(str(c_ref).lower())
                if c_data:
                    c_name = c_data.get("name", "character")
                    c_id_desc = c_data.get("visual_identity_description") or c_data.get("clothing", "")
                    char_desc_list.append(f"{c_name} ({c_id_desc})")

        characters_str = ""
        if char_desc_list:
            characters_str = f"featuring {', and '.join(char_desc_list)}, "

        # 4. Important Props & Objects
        props = scene.get("important_objects", [])
        props_str = ""
        if props:
            props_str = f", key focal items: {', '.join(props)}"

        # 5. Continuity anchors from previous scene
        continuity_str = ""
        if previous_scene:
            prev_env = previous_scene.get("environment")
            if prev_env and prev_env.lower() in environment.lower():
                continuity_str = ", maintaining continuous spatial environment and lighting"

        # 6. Assemble Positive Prompt
        # Format: [Framing] of [Characters] [Action] in [Environment], [Props], [Emotion], [Lighting], [Optics], [Continuity]
        positive_prompt = (
            f"{framing_desc} of {characters_str}{action.strip()} in {environment.strip()}{props_str}, "
            f"conveying palpable {emotion}, {lighting.strip()}{continuity_str}, {style_info['optics']}"
        )

        # 7. Assemble Negative Prompt
        negative_prompt = style_info["negative"]
        if "negative_prompt" in scene and scene["negative_prompt"]:
            negative_prompt = f"{scene['negative_prompt']}, {negative_prompt}"

        return positive_prompt, negative_prompt

    def _map_camera_framing(self, angle: str) -> str:
        """Map camera angle string to visual framing instruction."""
        ang = angle.lower()
        if "wide" in ang or "establishing" in ang:
            return "Cinematic wide establishing shot with vast environmental scale"
        if "close" in ang:
            return "Intimate cinematic close-up shot capturing emotional nuance and micro-expressions"
        if "extreme_macro" in ang or "macro" in ang:
            return "Extreme macro detail shot focusing on fine tactile textures and tangible clues"
        if "over_the_shoulder" in ang:
            return "Cinematic over-the-shoulder shot framing subject interaction with environment"
        return "Cinematic medium action shot emphasizing character posture and situational interaction"
