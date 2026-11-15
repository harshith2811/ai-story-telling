"""Main story service — orchestrates LLM calls, validation, and post-processing.

This is the primary entry-point that API routes should interact with.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from .json_validator import StoryValidationError, validate_story
from .prompts import (
    HOOK_EVALUATION_PROMPT,
    HOOK_GENERATION_PROMPT,
    STORY_GENERATION_PROMPT,
    STORY_QUALITY_PROMPT,
    STORY_REWRITE_PROMPT,
    STORY_SYSTEM_PROMPT,
)
from .provider import LLMProvider

logger = logging.getLogger(__name__)

# Rough words-per-second estimate for spoken narration.
_WPS = 2.5


class StoryService:
    """High-level service that wraps an :class:`LLMProvider` and exposes
    story-generation workflows consumed by the API layer.

    Parameters:
        provider: Any concrete ``LLMProvider`` implementation.
        default_temperature: Sampling temperature used unless overridden.
        default_max_tokens: Max generation tokens unless overridden.
    """

    def __init__(
        self,
        provider: LLMProvider,
        default_temperature: float = 0.8,
        default_max_tokens: int = 4000,
    ) -> None:
        self._provider = provider
        self._temperature = default_temperature
        self._max_tokens = default_max_tokens

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_story(self, request: dict[str, Any]) -> dict[str, Any]:
        """Full story-generation pipeline.

        1. Build prompt from *request* parameters.
        2. Call the LLM.
        3. Extract & validate the JSON response.
        4. Generate and evaluate hooks.
        5. Return the enriched story dict.

        Args:
            request: Dict with keys ``topic``, ``category``, ``language``,
                ``duration``, ``emotional_tone``, ``audience``.

        Returns:
            Validated story dict augmented with ``alternative_hooks`` and
            ``hook_scores``.
        """
        topic: str = request.get("topic", "a mysterious event")
        category: str = request.get("category", "general")
        language: str = request.get("language", "English")
        duration: int = int(request.get("duration", 120))
        emotional_tone: str = request.get("emotional_tone", "intriguing")
        audience: str = request.get("audience", "general")
        word_count = int(duration * _WPS)

        prompt = STORY_GENERATION_PROMPT.format(
            topic=topic,
            category=category,
            language=language,
            duration=duration,
            word_count=word_count,
            emotional_tone=emotional_tone,
            audience=audience,
        )

        logger.info("Generating story: topic=%s  duration=%ds", topic, duration)
        raw = await self._provider.generate(
            prompt=prompt,
            system_prompt=STORY_SYSTEM_PROMPT,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        story = self.validate_story_json(raw)

        # Inject persistent CharacterDNA consistency anchors across scenes
        char_dna = story.get("character_dna")
        if char_dna and "scenes" in story:
            try:
                from app.services.character_engine.character_service import CharacterService
                char_svc = CharacterService()
                story["scenes"] = char_svc.inject_character_dna_into_scenes(story["scenes"], char_dna)
            except Exception as exc:
                logger.debug("Character DNA injection skipped: %s", exc)

        # Generate alternative hooks & evaluate them in parallel-ish fashion.
        try:
            alt_hooks = await self.generate_hooks(
                story_text=self._story_to_plain_text(story),
                title=story.get("title", ""),
                topic=topic,
                original_hook=story.get("hook", ""),
                count=3,
            )
            # Collect all hook texts (original + alternatives) for evaluation.
            all_hook_texts = [story["hook"]] + [h.get("hook_text") or h.get("text", "") for h in alt_hooks]
            hook_scores = await self.evaluate_hooks(all_hook_texts)
        except Exception:
            logger.warning("Hook generation/evaluation failed; continuing without", exc_info=True)
            alt_hooks = []
            hook_scores = []

        story["alternative_hooks"] = alt_hooks
        story["hook_scores"] = hook_scores
        return story

    async def generate_hooks(
        self,
        story_text: str,
        title: str = "",
        topic: str = "",
        original_hook: str = "",
        count: int = 3,
    ) -> list[dict[str, Any]]:
        """Generate *count* alternative opening hooks for a story."""
        prompt = HOOK_GENERATION_PROMPT.format(
            title=title or "Inspirational Story",
            topic=topic or "Overcoming Adversity",
            original_hook=original_hook or "They said it was impossible.",
            story_summary=story_text[:400],
        )
        raw = await self._provider.generate(
            prompt=prompt,
            system_prompt=STORY_SYSTEM_PROMPT,
            temperature=self._temperature + 0.1,  # slightly more creative
            max_tokens=1000,
        )
        hooks = self._extract_json(raw)
        if not isinstance(hooks, list):
            raise ValueError("Expected a JSON array of hooks")
        return hooks

    async def evaluate_hooks(self, hooks: list[str]) -> list[dict[str, Any]]:
        """Score a list of hook strings across six quality dimensions."""
        hooks_json = json.dumps(
            [{"hook_number": i + 1, "text": h} for i, h in enumerate(hooks)],
            indent=2,
        )
        prompt = HOOK_EVALUATION_PROMPT.format(hooks_json=hooks_json)
        raw = await self._provider.generate(
            prompt=prompt,
            system_prompt=STORY_SYSTEM_PROMPT,
            temperature=0.3,  # low temp for analytical task
            max_tokens=2000,
        )
        scores = self._extract_json(raw)
        if not isinstance(scores, list):
            raise ValueError("Expected a JSON array of hook evaluations")
        return scores

    async def evaluate_story_quality(self, story: dict[str, Any]) -> dict[str, Any]:
        """Run a quality assessment on a validated story dict."""
        prompt = STORY_QUALITY_PROMPT.format(story_json=json.dumps(story, indent=2))
        raw = await self._provider.generate(
            prompt=prompt,
            system_prompt=STORY_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2000,
        )
        result = self._extract_json(raw)
        if not isinstance(result, dict):
            raise ValueError("Expected a JSON object for quality evaluation")
        return result

    async def rewrite_section(
        self,
        story: dict[str, Any],
        section: str,
        instructions: str,
    ) -> dict[str, Any]:
        """Rewrite a specific *section* of the story according to *instructions*.

        Returns:
            The complete, updated story dict (re-validated).
        """
        prompt = STORY_REWRITE_PROMPT.format(
            story_json=json.dumps(story, indent=2),
            section=section,
            instructions=instructions,
        )
        raw = await self._provider.generate(
            prompt=prompt,
            system_prompt=STORY_SYSTEM_PROMPT,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return self.validate_story_json(raw)

    # ------------------------------------------------------------------
    # JSON extraction & validation helpers
    # ------------------------------------------------------------------

    def validate_story_json(self, raw: str) -> dict[str, Any]:
        """Parse raw LLM output into a validated story dict.

        Handles common LLM quirks:
        - Markdown code fences (```json ... ```)
        - Leading/trailing prose around the JSON block
        - Partial or truncated JSON (best-effort recovery)

        Raises:
            ValueError: If no valid JSON can be extracted.
            StoryValidationError: If JSON parses but fails schema checks.
        """
        data = self._extract_json(raw)
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object at the top level, got {type(data).__name__}"
            )
        return validate_story(data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Best-effort extraction of a JSON value from possibly-noisy LLM text.

        Strategy (in order):
        1. Try parsing the entire text directly.
        2. Strip markdown code fences and retry.
        3. Find the first ``{`` or ``[`` and the last matching ``}`` or ``]``,
           then attempt to parse that substring.
        4. Try to repair common trailing-truncation by appending closing
           braces/brackets.

        Returns:
            The parsed Python object (dict or list).

        Raises:
            ValueError: If all strategies fail.
        """
        # Strategy 1 — raw parse
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2 — strip markdown fences
        stripped = _strip_code_fences(text)
        if stripped != text:
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                pass

        # Strategy 3 — locate outermost JSON structure
        candidate = _find_json_substring(stripped)
        if candidate:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Strategy 4 — attempt truncation repair on the candidate
        if candidate:
            repaired = _repair_truncated_json(candidate)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass

        raise ValueError(
            "Could not extract valid JSON from LLM response. "
            f"First 200 chars: {text[:200]!r}"
        )

    @staticmethod
    def _story_to_plain_text(story: dict[str, Any]) -> str:
        """Flatten a story dict into plain narrative text for prompt injection."""
        parts: list[str] = []
        parts.append(story.get("title", ""))
        for scene in story.get("scenes", []):
            parts.append(scene.get("content", ""))
        return "\n\n".join(parts)


# ======================================================================
# Module-private JSON-repair utilities
# ======================================================================

_CODE_FENCE_RE = re.compile(
    r"```(?:json|JSON)?\s*\n?(.*?)\n?\s*```",
    re.DOTALL,
)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences and return the inner content."""
    match = _CODE_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


def _find_json_substring(text: str) -> str | None:
    """Return the substring from the first ``{``/``[`` to the last matching
    ``}``/``]``, or *None* if not found."""
    # Find first opening bracket
    obj_start = text.find("{")
    arr_start = text.find("[")

    if obj_start == -1 and arr_start == -1:
        return None

    if obj_start == -1:
        start = arr_start
        close = "]"
    elif arr_start == -1:
        start = obj_start
        close = "}"
    else:
        if obj_start <= arr_start:
            start = obj_start
            close = "}"
        else:
            start = arr_start
            close = "]"

    end = text.rfind(close)
    if end <= start:
        # No matching close — return from start to end of string for repair.
        return text[start:]
    return text[start : end + 1]


def _repair_truncated_json(text: str) -> str | None:
    """Attempt to close unclosed braces/brackets from a truncated JSON string.

    Handles the common case where the LLM's output was cut off mid-object.
    """
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            open_braces += 1
        elif ch == "}":
            open_braces -= 1
        elif ch == "[":
            open_brackets += 1
        elif ch == "]":
            open_brackets -= 1

    if open_braces == 0 and open_brackets == 0:
        return text  # already balanced

    # Strip a possible trailing partial key/value (after last comma or colon).
    # Find the last structurally complete position.
    trimmed = text.rstrip()
    # Remove trailing comma if present.
    if trimmed.endswith(","):
        trimmed = trimmed[:-1]

    suffix = "]" * max(0, open_brackets) + "}" * max(0, open_braces)
    return trimmed + suffix
