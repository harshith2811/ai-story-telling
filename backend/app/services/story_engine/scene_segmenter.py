"""
StoryForge AI - Intelligent Scene Segmentation Engine

Segments narrative stories into meaningful visual events rather than word counts:
- Establishes location and spatial context with wide establishing shots
- Transitions to medium shots for character interaction and physical action
- Focuses close-ups on high-stakes emotional beats and critical narrative turning points
- Dynamically allocates scene durations according to spoken narration and action complexity
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Average speaking rate: 2.3 to 2.6 words per second
WORDS_PER_SECOND = 2.4
MIN_SCENE_DURATION = 3.5
MAX_SCENE_DURATION = 12.0


class SceneSegmenter:
    """Intelligent visual scene segmentation adhering to film directing principles."""

    def __init__(self, target_duration: float = 60.0):
        self.target_duration = target_duration

    def segment_story_into_visual_beats(
        self,
        story_text: str,
        character_names: Optional[List[str]] = None,
        target_scene_count: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Segment story text into structured visual scenes with explicit directorial intent."""
        clean_text = story_text.strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text) if s.strip()]
        if not sentences:
            sentences = [clean_text]

        # Determine optimal scene count (4 to 8 scenes for vertical short-form)
        if target_scene_count:
            num_scenes = target_scene_count
        else:
            word_count = len(clean_text.split())
            if word_count < 60:
                num_scenes = 4
            elif word_count < 130:
                num_scenes = 5
            elif word_count < 200:
                num_scenes = 6
            else:
                num_scenes = min(8, max(5, word_count // 35))

        # Cluster sentences by visual/emotional shift rather than raw word count
        sentence_clusters = self._cluster_sentences(sentences, num_scenes)

        scenes: List[Dict[str, Any]] = []
        for idx, cluster in enumerate(sentence_clusters, start=1):
            narration = " ".join(cluster)
            words = len(narration.split())
            spoken_duration = max(MIN_SCENE_DURATION, words / WORDS_PER_SECOND)

            # Assign directorial shot scale based on narrative position and content
            shot_type, camera_movement = self._direct_shot_scale(idx, len(sentence_clusters), narration)

            scenes.append({
                "scene_id": idx,
                "scene_number": idx,
                "narration": narration,
                "story_text": narration,
                "word_count": words,
                "duration": round(spoken_duration, 2),
                "camera_angle": shot_type,
                "camera_movement": camera_movement,
                "visual_purpose": self._determine_visual_purpose(idx, len(sentence_clusters)),
            })

        # Scale durations to harmonize with target total duration
        scenes = self.balance_scene_durations(scenes, self.target_duration)
        return scenes

    def _cluster_sentences(self, sentences: List[str], target_clusters: int) -> List[List[str]]:
        """Cluster sentences by natural narrative shifts, subdividing by clauses if needed."""
        # If we have fewer sentences than the requested target clusters, break into visual clauses
        if len(sentences) < target_clusters:
            expanded: List[str] = []
            for s in sentences:
                parts = [p.strip() for p in re.split(r"[,;—]|\b(?:and then|and|as|while|until)\b", s) if len(p.strip().split()) >= 2]
                if len(parts) > 1 and len(expanded) + len(parts) <= target_clusters + 2:
                    expanded.extend(parts)
                else:
                    expanded.append(s)
            if len(expanded) >= target_clusters:
                sentences = expanded

        if len(sentences) <= target_clusters:
            return [[s] for s in sentences]

        total_words = sum(len(s.split()) for s in sentences)
        words_per_cluster = total_words / target_clusters

        clusters: List[List[str]] = []
        current_cluster: List[str] = []
        current_word_count = 0

        for s in sentences:
            s_words = len(s.split())
            current_cluster.append(s)
            current_word_count += s_words

            # If reached target cluster size and not on last cluster
            if (
                current_word_count >= words_per_cluster
                and len(clusters) < target_clusters - 1
            ):
                clusters.append(current_cluster)
                current_cluster = []
                current_word_count = 0

        if current_cluster:
            if clusters and len(clusters) == target_clusters:
                clusters[-1].extend(current_cluster)
            else:
                clusters.append(current_cluster)

        return clusters

    def _direct_shot_scale(self, index: int, total: int, narration: str) -> tuple[str, str]:
        """Select camera angle and movement based on cinematic storytelling rules."""
        text_lower = narration.lower()

        # Scene 1: Always Wide Establishing to set the world and scale
        if index == 1:
            return "wide_establishing", "slow_zoom_in"

        # Emotional peak / Climax (Penultimate or high-emotion scene): Close-up
        if index == total - 1 or any(w in text_lower for w in ["cried", "whispered", "tears", "eyes", "heart", "gasped", "shock", "horror"]):
            return "close_up_emotion", "slow_zoom_in"

        # Final scene: Wide Atmospheric or Over-the-shoulder for lingering reflection
        if index == total:
            return "wide_atmospheric_silhouette", "pan_right"

        # Technical/Clue details
        if any(w in text_lower for w in ["revealed", "read", "screen", "dial", "device", "photograph", "letter", "wound", "sparrow"]):
            return "extreme_macro_detail", "slow_zoom_in"

        # Default Middle: Medium Action / Two-Shot
        return "medium_action", "slow_zoom_in"

    def _determine_visual_purpose(self, index: int, total: int) -> str:
        """Classify the storytelling purpose of this scene beat."""
        if index == 1:
            return "Establish world, physical environment, and immediate curiosity hook"
        if index == 2:
            return "Escalate physical situation, introduce tangible obstacle or evidence"
        if index == total - 1:
            return "Climax and paradigm snap; reveal the core unexpected truth"
        if index == total:
            return "Aftermath and unresolved dilemma; prompt audience comment engagement"
        return "Deepen human stakes and character conflict"

    def balance_scene_durations(
        self, scenes: List[Dict[str, Any]], target_total: float
    ) -> List[Dict[str, Any]]:
        """Normalize and scale durations across scenes while respecting minimum speech lengths."""
        if not scenes:
            return []

        current_sum = sum(s["duration"] for s in scenes)
        if current_sum <= 0:
            current_sum = len(scenes) * 5.0

        scale = target_total / current_sum

        for sc in scenes:
            scaled = sc["duration"] * scale
            # Clamp between MIN and MAX
            sc["duration"] = round(max(MIN_SCENE_DURATION, min(MAX_SCENE_DURATION, scaled)), 2)

        return scenes
