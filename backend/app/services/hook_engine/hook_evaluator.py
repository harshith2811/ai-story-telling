"""
StoryForge AI - Hook Intelligence & Evaluation Engine

Generates multiple opening hooks and evaluates them using a transparent
heuristic scoring framework across 6 key short-form retention dimensions.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.services.story_engine.prompts import (
    HOOK_EVALUATION_PROMPT,
    HOOK_GENERATION_PROMPT,
    STORY_SYSTEM_PROMPT,
)
from app.services.story_engine.provider import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)


class HookEvaluator:
    """Heuristic hook evaluation and generation engine."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    async def generate_alternative_hooks(
        self, title: str, topic: str, original_hook: str, story_summary: str
    ) -> list[dict[str, Any]]:
        """Generate 3 distinct opening hook variations (curiosity, in media res, emotional punch)."""
        prompt = HOOK_GENERATION_PROMPT.format(
            title=title,
            topic=topic,
            original_hook=original_hook,
            story_summary=story_summary,
        )
        raw = await self.provider.generate(prompt=prompt, system_prompt=STORY_SYSTEM_PROMPT, temperature=0.85)

        try:
            # Clean markdown if present
            clean = raw.strip()
            if "```" in clean:
                clean = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", clean).strip()
            hooks = json.loads(clean)
            if isinstance(hooks, list) and len(hooks) > 0:
                return hooks
        except Exception as exc:
            logger.warning("Failed to parse LLM hooks (%s), using heuristic fallbacks.", exc)

        # Transparent heuristic fallback hooks
        return [
            {
                "hook_text": f"What if everything you were told about {topic} was completely wrong?",
                "hook_type": "curiosity",
                "explanation": "Triggers immediate cognitive curiosity and counterintuitive thinking."
            },
            {
                "hook_text": f"He had 10 seconds to make the decision that would either ruin his life or change history.",
                "hook_type": "in_media_res",
                "explanation": "Drops the audience directly into a high-stakes moment of tension."
            },
            {
                "hook_text": f"The painful secret nobody talks about when fighting for their dreams.",
                "hook_type": "emotional_punch",
                "explanation": "Touches a deep nerve of empathy and vulnerability."
            }
        ]

    async def evaluate_hook(self, hook_text: str, topic: str) -> dict[str, Any]:
        """Score a hook on a transparent 0-100 scale across 6 dimensions.
        
        The score is an internal ranking estimate based on structural heuristics,
        never a guarantee of virality.
        """
        # Calculate algorithmic heuristic baseline
        heuristic_scores = self._calculate_algorithmic_scores(hook_text)

        prompt = HOOK_EVALUATION_PROMPT.format(hook_text=hook_text, topic=topic)
        try:
            raw = await self.provider.generate(prompt=prompt, system_prompt=STORY_SYSTEM_PROMPT, temperature=0.3)
            clean = raw.strip()
            if "```" in clean:
                clean = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", clean).strip()
            llm_eval = json.loads(clean)
            if isinstance(llm_eval, dict) and "overall_score" in llm_eval:
                return llm_eval
        except Exception as exc:
            logger.debug("LLM hook eval fallback to algorithmic scoring: %s", exc)

        # Calculate weighted average from algorithmic heuristics
        weights = {
            "curiosity": 0.20,
            "emotional_impact": 0.20,
            "clarity": 0.20,
            "relevance": 0.15,
            "originality": 0.15,
            "immediate_attention": 0.10,
        }
        weighted_sum = sum(heuristic_scores[k] * weights[k] for k in weights)
        overall = int(round(weighted_sum))

        return {
            "overall_score": overall,
            "scores": heuristic_scores,
            "strengths": [
                "Concise opening phrasing tailored for the 3-second scroll test",
                "Strong emotional or curiosity pull in the opening words"
            ],
            "weaknesses": [
                "Ensure physical gestures or visuals in Scene 1 complement this hook instantly"
            ],
            "improvement_suggestion": "Deliver this line with a slight pause right before the punch word."
        }

    def _calculate_algorithmic_scores(self, hook: str) -> dict[str, int]:
        """Deterministic NLP heuristic scoring for hooks."""
        hook_lower = hook.lower().strip()
        words = hook.split()
        word_count = len(words)

        # Clarity: optimal hook length is 8 to 18 words
        if 8 <= word_count <= 18:
            clarity = 92
        elif 5 <= word_count < 8:
            clarity = 85
        elif 19 <= word_count <= 25:
            clarity = 78
        else:
            clarity = 65

        # Curiosity signals
        curiosity_triggers = ["why", "how", "secret", "never", "nobody", "what if", "before", "truth", "discovered", "hidden"]
        curiosity_matches = sum(1 for w in curiosity_triggers if w in hook_lower)
        curiosity = min(98, 70 + (curiosity_matches * 9))

        # Emotional signals
        emotional_words = ["tears", "pain", "cried", "heart", "dream", "ruin", "refuse", "quit", "miracle", "broke", "loss", "love", "passion"]
        emo_matches = sum(1 for w in emotional_words if w in hook_lower)
        emotional_impact = min(96, 68 + (emo_matches * 10))

        # Immediate attention signals (first 3 words)
        first_three = " ".join(words[:3]).lower() if len(words) >= 3 else hook_lower
        attention_boosters = ["stop", "they told", "never", "before you", "this is", "what happens", "he had", "she had", "imagine"]
        immediate = 88 if any(b in first_three for b in attention_boosters) else 78

        # Originality: penalize cliché platitudes
        cliches = ["never give up", "hard work pays off", "believe in yourself", "follow your dreams"]
        penalty = 15 if any(c in hook_lower for c in cliches) else 0
        originality = max(60, 85 - penalty)

        relevance = 88

        return {
            "curiosity": curiosity,
            "emotional_impact": emotional_impact,
            "clarity": clarity,
            "relevance": relevance,
            "originality": originality,
            "immediate_attention": immediate,
        }
