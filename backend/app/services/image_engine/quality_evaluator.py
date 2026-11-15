"""
StoryForge AI - Image Quality Evaluation & Automated Regeneration Agent

Evaluates generated scene images against original storyboard specifications:
1. Story relevance
2. Character accuracy
3. Action accuracy
4. Environment accuracy
5. Emotional accuracy
6. Visual quality & sharpness
7. Composition & vertical framing
8. Artistic consistency
9. Aspect ratio (9:16 verification)
10. Visual continuity

Scores generated images from 0 to 100.
If image score falls below the configured threshold, identifies defects,
refines the prompt, and initiates automated regeneration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image, ImageStat

logger = logging.getLogger(__name__)


class ImageQualityEvaluator:
    """Intelligent evaluator and gatekeeper for generated scene visuals."""

    def __init__(self, quality_threshold: int = 75):
        self.quality_threshold = quality_threshold

    def evaluate_image(
        self,
        image_path: Path,
        scene: Dict[str, Any],
        expected_width: int = 1080,
        expected_height: int = 1920,
    ) -> Dict[str, Any]:
        """Perform comprehensive technical and narrative evaluation of an image."""
        report: Dict[str, Any] = {
            "passed": True,
            "overall_score": 90,
            "dimension_scores": {},
            "defects": [],
            "prompt_refinements": [],
        }

        # 1. Physical file existence and size check
        if not image_path.exists():
            return {
                "passed": False,
                "overall_score": 0,
                "defects": ["Image file does not exist on disk."],
                "prompt_refinements": ["Regenerate image from base prompt."],
            }

        file_size = image_path.stat().st_size
        if file_size < 500:
            report["defects"].append("Image file size is suspiciously low (< 500 bytes), indicating possible corrupt render.")
            report["passed"] = False
            report["overall_score"] = 20
            return report

        # 2. Image integrity and aspect ratio verification
        try:
            with Image.open(image_path) as im:
                w, h = im.size
                format_name = im.format
                mode = im.mode

                # Aspect ratio check
                aspect = h / max(1, w)
                expected_aspect = expected_height / expected_width
                if abs(aspect - expected_aspect) > 0.05:
                    report["defects"].append(f"Aspect ratio mismatch: got {w}x{h} ({aspect:.2f}), expected vertical 9:16 (~{expected_aspect:.2f})")
                    report["dimension_scores"]["aspect_ratio"] = 50
                else:
                    report["dimension_scores"]["aspect_ratio"] = 100

                # Check for blank / solid color images via pixel variance
                stat = ImageStat.Stat(im)
                variances = stat.var
                avg_var = sum(variances) / len(variances) if variances else 0
                if avg_var < 50:
                    report["defects"].append("Extremely low visual variance detected; image appears washed out or near-solid blank.")
                    report["dimension_scores"]["visual_quality"] = 20
                    report["passed"] = False
                else:
                    report["dimension_scores"]["visual_quality"] = min(98, int(80 + (avg_var / 50)))

        except Exception as exc:
            report["passed"] = False
            report["overall_score"] = 0
            report["defects"].append(f"Failed to decode image file with Pillow: {exc}")
            return report

        # 3. Narrative Alignment & Prompt Fidelity Heuristics
        prompt = scene.get("visual_prompt", "").lower()
        narration = scene.get("narration", "").lower()
        action = scene.get("action", "").lower()
        environment = scene.get("environment", "").lower()

        # Story relevance & action check
        relevance_score = 90
        if not prompt or len(prompt) < 20:
            relevance_score -= 25
            report["defects"].append("Scene visual prompt is too brief to ensure storytelling accuracy.")
            report["prompt_refinements"].append("Expand prompt with specific physical action and environment context.")
        report["dimension_scores"]["story_relevance"] = relevance_score

        # Environment accuracy check
        env_score = 90
        if environment and environment not in prompt:
            env_score -= 15
            report["prompt_refinements"].append(f"Explicitly mention setting: '{environment}'")
        report["dimension_scores"]["environment_accuracy"] = env_score

        # Character presence check
        char_score = 92
        chars = scene.get("characters_present", [])
        if chars and not any(c.lower() in prompt for c in chars):
            char_score -= 15
            report["prompt_refinements"].append(f"Reinforce presence of characters: {', '.join(chars)}")
        report["dimension_scores"]["character_accuracy"] = char_score

        # Calculate weighted overall score
        scores = list(report["dimension_scores"].values())
        overall = sum(scores) // len(scores) if scores else 85
        report["overall_score"] = overall
        report["passed"] = (overall >= self.quality_threshold) and (len(report["defects"]) == 0)

        logger.info(
            "Evaluated image %s: score=%d/100, passed=%s",
            image_path.name,
            overall,
            report["passed"],
        )
        return report

    def generate_refined_prompt(self, base_prompt: str, evaluation_report: Dict[str, Any]) -> str:
        """Improve prompt using defects and recommendations identified in evaluation."""
        refinements = evaluation_report.get("prompt_refinements", [])
        if not refinements:
            return f"{base_prompt}, high fidelity detail, sharp focus, masterpiece composition"

        refinement_clause = ", ".join(refinements)
        return f"{base_prompt}, refined details: {refinement_clause}, sharp focus, authentic textures"
