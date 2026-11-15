"""
Automated Tests for Story Generation, JSON Validation, Hook Intelligence & Quality Audits
"""

import pytest
from app.services.story_engine.json_validator import StoryValidationError, validate_story, extract_json_from_text
from app.services.story_engine.provider import OfflineHeuristicProvider
from app.services.story_engine import StoryEngine
from app.services.hook_engine.hook_evaluator import HookEvaluator
from app.services.hook_engine.quality_evaluator import StoryQualityEvaluator


@pytest.mark.asyncio
async def test_story_generation_schema_validation():
    """Verify generated story conforms to structured JSON with all required fields."""
    provider = OfflineHeuristicProvider()
    engine = StoryEngine(provider=provider)

    story = await engine.generate_story({
        "topic": "The shoemaker who built a global brand",
        "category": "success_stories",
        "language": "English",
        "duration": 60,
        "emotional_tone": "determination",
        "audience": "general",
    })

    assert "title" in story
    assert "hook" in story
    assert "story" in story
    assert "moral" in story
    assert "scenes" in story
    assert len(story["scenes"]) >= 4

    for sc in story["scenes"]:
        assert "scene_number" in sc
        assert "narration" in sc
        assert "visual_prompt" in sc
        assert "camera_movement" in sc
        assert sc["duration"] >= 2.0


def test_invalid_json_handling():
    """Ensure malformed or incomplete JSON raises StoryValidationError."""
    with pytest.raises(StoryValidationError):
        extract_json_from_text("Invalid text with no JSON anywhere")

    with pytest.raises(StoryValidationError):
        validate_story({"title": "Test", "scenes": []})  # Empty scenes


@pytest.mark.asyncio
async def test_hook_generation_and_scoring():
    """Ensure 3 distinct hooks are generated and transparently scored 0-100."""
    evaluator = HookEvaluator()
    hooks = await evaluator.generate_alternative_hooks(
        title="The Impossible Climb",
        topic="mountain climber survival",
        original_hook="He was stranded at 20,000 feet with zero oxygen.",
        story_summary="A climber endures frostbite and makes an unprecedented descent."
    )

    assert len(hooks) >= 3
    for h in hooks:
        assert "hook_text" in h
        assert "hook_type" in h

    # Test transparent scoring
    scorecard = await evaluator.evaluate_hook(hooks[0]["hook_text"], "mountain climber survival")
    assert 0 <= scorecard["overall_score"] <= 100
    assert "scores" in scorecard
    assert "curiosity" in scorecard["scores"]
    assert "emotional_impact" in scorecard["scores"]
    assert "clarity" in scorecard["scores"]


@pytest.mark.asyncio
async def test_story_quality_auditor():
    """Verify story quality evaluation checks pacing, narrative arc, and duration."""
    evaluator = StoryQualityEvaluator()
    sample_script = "He started with nothing in his pockets. Every critic told him to give up. But he worked through the night. Today his work inspires millions."
    scenes = [{"scene_number": 1, "duration": 5.0}, {"scene_number": 2, "duration": 5.0}]

    audit = await evaluator.audit_story(
        title="Test Story",
        duration=30.0,
        story_script=sample_script,
        scenes=scenes,
    )

    assert "quality_score" in audit
    assert 0 <= audit["quality_score"] <= 100
    assert "verdict" in audit
    assert "critique" in audit
    assert "pacing_fit_score" in audit["critique"]
