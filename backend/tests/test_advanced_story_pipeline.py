"""
Comprehensive Test Suite for Advanced Story-to-Video Engine Optimization
Verifies:
1. Deep Story Understanding & Narrative Analysis (StoryAnalyzer)
2. Intelligent Scene Segmentation by visual moments (SceneSegmenter)
3. Character Bible & Multi-Character Consistency Engine (CharacterService)
4. Advanced Scene-to-Image Prompt Synthesizer & Visual Styles (ScenePromptSynthesizer)
5. Visual Continuity Engine across consecutive cuts (ContinuityEngine)
6. Image Quality Evaluation Agent & Scoring (ImageQualityEvaluator)
7. End-to-end multi-genre validation: Inspirational, Emotional, Animal, Historical, Fantasy
"""

import io
from pathlib import Path
import pytest
from PIL import Image

from app.services.character_engine.character_service import CharacterService
from app.services.image_engine.continuity_engine import ContinuityEngine
from app.services.image_engine.prompt_synthesizer import ScenePromptSynthesizer, VisualStyleRegistry
from app.services.image_engine.quality_evaluator import ImageQualityEvaluator
from app.services.story_engine.provider import OfflineHeuristicProvider
from app.services.story_engine.scene_segmenter import SceneSegmenter
from app.services.story_engine.story_analyzer import StoryAnalyzer


# ── 1. Story Understanding & Analysis ────────────────────────────────────────

@pytest.mark.asyncio
async def test_story_analyzer_decomposition():
    """Verify deep story analyzer extracts characters, narrative arc, and structured scenes."""
    provider = OfflineHeuristicProvider()
    analyzer = StoryAnalyzer(provider=provider)

    story_text = (
        "An old Indian craftsman named Kabir discovers a tiny injured sparrow on wet stone pavement during a sudden downpour. "
        "With trembling hands, he shelters the shivering creature beneath his woolen jacket and carries it into his workshop. "
        "Through careful warmth and healing, the bird regains its strength and takes flight at sunrise."
    )

    blueprint = await analyzer.analyze_story(
        story_text=story_text,
        title="The Craftsman and the Sparrow",
        genre="Emotional",
        visual_style="Cinematic realism",
        duration=45,
    )

    assert "story_title" in blueprint
    assert "character_bible" in blueprint
    assert len(blueprint["character_bible"]) >= 1
    assert "scenes" in blueprint
    assert len(blueprint["scenes"]) >= 3

    # Verify scene properties
    sc1 = blueprint["scenes"][0]
    assert "narration" in sc1
    assert "visual_description" in sc1
    assert "camera_angle" in sc1
    assert "duration" in sc1


# ── 2. Scene Segmentation by Visual Events ────────────────────────────────────

def test_scene_segmentation_rules():
    """Verify scene segmentation partitions by visual beats and enforces directorial shot progression."""
    segmenter = SceneSegmenter(target_duration=60.0)

    story_text = (
        "In the frozen mountains of Tibet, an elderly monk climbs the steep rocky ridge. "
        "He reaches an ancient shrine overlooking a boundless sea of clouds. "
        "Suddenly, a rare snow leopard appears silently on the opposite boulder. "
        "The monk kneels in deep reverent silence as their eyes meet. "
        "The majestic beast turns peacefully into the mist, leaving a single paw print in the fresh snow."
    )

    scenes = segmenter.segment_story_into_visual_beats(story_text)
    assert len(scenes) >= 4

    # Scene 1 must be wide establishing
    assert "wide" in scenes[0]["camera_angle"].lower()

    # Total duration should balance near target
    total_dur = sum(s["duration"] for s in scenes)
    assert 50.0 <= total_dur <= 70.0


# ── 3. Character Bible & Consistency ──────────────────────────────────────────

def test_character_bible_persistence(tmp_path):
    """Verify permanent character bible serialization and multi-character anchoring."""
    char_svc = CharacterService(storage_dir=tmp_path)

    story_data = {
        "character_bible": [
            {
                "character_id": "char_1",
                "name": "Kabir",
                "role": "Protagonist",
                "age": "65 years old",
                "facial_features": "White beard, deep crow's feet, warm compassionate eyes",
                "clothing": "Brown wool jacket over faded cream tunic",
                "accessories": "Carved wooden pendant",
            },
            {
                "character_id": "char_2",
                "name": "Maya",
                "role": "Supporting",
                "age": "10 years old",
                "facial_features": "Curious bright brown eyes, black braided hair",
                "clothing": "Yellow rain poncho",
                "accessories": "Small red satchel",
            },
        ]
    }

    bible = char_svc.build_character_bible(story_data)
    assert len(bible) == 2
    assert bible[0]["character_id"] == "char_1"
    assert "65 years old" in bible[0]["visual_identity_description"]

    # Test file persistence
    saved_path = char_svc.save_character_bible(project_id=888, bible=bible)
    assert saved_path.exists()

    loaded = char_svc.load_character_bible(project_id=888)
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[1]["name"] == "Maya"


# ── 4. Advanced Prompt Synthesizer & Visual Styles ────────────────────────────

def test_scene_prompt_synthesizer_multi_style():
    """Verify prompt synthesis handles character actions, environments, and multiple artistic styles."""
    synthesizer = ScenePromptSynthesizer()

    character_bible = [
        {
            "character_id": "char_1",
            "name": "Arthur",
            "visual_identity_description": "64-year-old watchmaker Arthur, silver stubble, brass loupe on eye, olive tweed waistcoat",
        }
    ]

    scene = {
        "scene_id": 1,
        "action": "kneeling beside a shattered clock on wet cobblestones",
        "environment": "a dimly lit Victorian London alley during rain",
        "emotion": "dread and urgency",
        "camera_angle": "medium_action",
        "lighting": "amber gaslamp chiaroscuro with wet reflective sheen",
        "important_objects": ["brass pocket watch"],
        "characters_present": ["char_1"],
    }

    # Style 1: Cinematic Realism
    pos_cine, neg_cine = synthesizer.synthesize_prompt(scene, character_bible, visual_style="cinematic_realism")
    assert "Arthur" in pos_cine
    assert "kneeling beside a shattered clock" in pos_cine
    assert "ARRI Alexa 65" in pos_cine
    assert "no static passport headshot" in neg_cine

    # Style 2: Anime / Studio Ghibli
    pos_anime, neg_anime = synthesizer.synthesize_prompt(scene, character_bible, visual_style="anime")
    assert "Studio Ghibli" in pos_anime
    assert "cel-shaded" in pos_anime
    assert "no 3D CGI plastic render" in neg_anime

    # Style 3: Pixar 3D
    pos_pixar, neg_pixar = synthesizer.synthesize_prompt(scene, character_bible, visual_style="pixar_3d")
    assert "Pixar" in pos_pixar
    assert "subsurface scattering" in pos_pixar


# ── 5. Visual Continuity Engine ───────────────────────────────────────────────

def test_visual_continuity_detection():
    """Verify continuity engine audits weather, props, and wardrobe between adjacent cuts."""
    continuity = ContinuityEngine()

    scene_1 = {
        "scene_id": 1,
        "environment": "cobblestone street in heavy rain at night",
        "important_objects": ["glowing red compass"],
        "visual_prompt": "A traveler in a worn brown leather trenchcoat holding a glowing red compass in rain",
    }

    scene_2_missing_rain = {
        "scene_id": 2,
        "environment": "cobblestone street outside a library door",
        "important_objects": ["glowing red compass"],
        "visual_prompt": "A traveler unlocking an ancient wooden door",
    }

    audit = continuity.validate_scene_continuity(scene_2_missing_rain, previous_scene=scene_1)
    assert not audit["is_continuous"]
    assert any("rain" in s.lower() for s in audit["continuity_injections"])
    assert any("glowing red compass" in s for s in audit["continuity_injections"])

    # Test prompt enrichment with continuity
    enriched = continuity.enrich_prompt_with_continuity("Base action prompt", scene_2_missing_rain, scene_1)
    assert "continuity:" in enriched
    assert "rain" in enriched.lower()


# ── 6. Image Quality Evaluation Agent ─────────────────────────────────────────

def test_image_quality_evaluator(tmp_path):
    """Verify quality evaluator assesses aspect ratio, image entropy, and narrative fidelity."""
    evaluator = ImageQualityEvaluator(quality_threshold=75)

    # 1. Create a valid vertical 1080x1920 image with realistic gradient variance
    good_img_path = tmp_path / "valid_image.png"
    im = Image.new("RGB", (1080, 1920))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(im)
    for y in range(0, 1920, 10):
        r = int(255 * (y / 1920))
        g = int(128 * (1 - y / 1920))
        b = (y * 3) % 255
        draw.line([(0, y), (1080, y)], fill=(r, g, b))
    im.save(good_img_path)

    scene = {
        "visual_prompt": "A dramatic vertical 9:16 shot of an astronomer inside an observatory dome at twilight",
        "narration": "He gazed out into the twilight sky.",
        "environment": "observatory dome",
        "action": "gazing into twilight",
    }

    report = evaluator.evaluate_image(good_img_path, scene, expected_width=1080, expected_height=1920)
    assert report["passed"] is True
    assert report["overall_score"] >= 75
    assert report["dimension_scores"]["aspect_ratio"] == 100

    # 2. Test horizontal aspect ratio failure
    bad_img_path = tmp_path / "bad_ratio.png"
    bad_im = Image.new("RGB", (1920, 1080), color=(50, 50, 50))
    bad_im.save(bad_img_path)

    bad_report = evaluator.evaluate_image(bad_img_path, scene, expected_width=1080, expected_height=1920)
    assert bad_report["passed"] is False
    assert any("Aspect ratio mismatch" in d for d in bad_report["defects"])


# ── 7. Multi-Genre Validation ─────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("genre,sample_story", [
    (
        "Inspirational",
        "A young female runner with a prosthetic leg trains through dawn blizzards. "
        "She pushes past exhaustion on icy mountain roads. "
        "On the final stretch of the national marathon, her determination electrifies the roaring crowd. "
        "She crosses the finish line in tears of triumph."
    ),
    (
        "Emotional",
        "An elderly grandfather builds a wooden sailboat in his dust-filled workshop for his sick grandson. "
        "Night after night, he polishes the cedar hull under a warm hanging lamp. "
        "He delivers the completed vessel to the boy's bedside at sunset. "
        "Together, their hands rest on the wooden helm with renewed hope."
    ),
    (
        "Animal",
        "A stray golden retriever wanders through a bustling city during a sudden thunderous downpour. "
        "Beneath an abandoned car, he discovers a shivering kitten trapped in the rising water. "
        "Gently carrying the kitten by its scruff, the dog sprints through splashing traffic. "
        "He deposits the kitten safely into the warm arms of a shelter volunteer."
    ),
    (
        "Historical",
        "In December 1911, explorer Roald Amundsen and his crew march across the vast blinding white Antarctic ice shelf. "
        "Crevasse fields threaten to swallow their dogs and wooden sledges at every step. "
        "Through howling sub-zero blizzards, they press forward toward the southern pole. "
        "Finally, they plant Norway's crimson flag firmly into the barren polar snow."
    ),
    (
        "Fantasy",
        "In a hidden underground cavern, an apprentice alchemist accidentally miscalculates an ancient solar rune. "
        "A blinding miniature star ignites above his brass alembic, bathing the dark cavern in golden fire. "
        "The radiant glow illuminates towering stone shelves holding thousands of forgotten elven scrolls. "
        "The apprentice stares in awe as ancient celestial constellations swirl across the stone ceiling."
    ),
])
async def test_multi_genre_story_processing(genre, sample_story):
    """Verify story decomposition, character bible, and segmentation across all 5 core genres."""
    provider = OfflineHeuristicProvider()
    analyzer = StoryAnalyzer(provider=provider)
    segmenter = SceneSegmenter(target_duration=45.0)

    blueprint = await analyzer.analyze_story(
        story_text=sample_story,
        genre=genre,
        duration=45,
    )

    assert blueprint["genre"] is not None
    assert len(blueprint["character_bible"]) >= 1
    assert len(blueprint["scenes"]) >= 3

    # Segment scenes and ensure shot variety
    beats = segmenter.segment_story_into_visual_beats(sample_story, target_scene_count=4)
    assert len(beats) == 4
    assert beats[0]["camera_angle"] == "wide_establishing"
