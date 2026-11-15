"""
Automated Tests for Character Consistency Engine
"""

from app.services.character_engine.character_service import CharacterService


def test_character_extraction_and_normalization():
    """Verify character extraction and consistent profile normalization."""
    service = CharacterService()
    story_payload = {
        "title": "The Weaver's Daughter",
        "topic": "traditional craftsmanship",
        "characters": [
            {
                "name": "Maya",
                "role": "Master Weaver",
                "visual_description": "22-year-old woman with braided dark hair and warm brown eyes",
                "costume": "Handwoven saffron silk tunic with embroidered hem",
            }
        ]
    }

    profiles = service.extract_characters_from_story(story_payload)
    assert len(profiles) == 1
    p = profiles[0]
    assert p["name"] == "Maya"
    assert "reference_prompt" in p
    assert "Maya" in p["reference_prompt"]
    assert "saffron silk" in p["reference_prompt"]


def test_character_prompt_injection():
    """Verify character anchor tags are injected into scene prompts for consistency."""
    service = CharacterService()
    profile = {
        "name": "David",
        "visual_description": "28-year-old architect with thin wireframe glasses",
        "costume": "Dark navy trench coat and slate grey trousers",
    }

    base_prompt = "Standing on a rainy balcony overlooking Paris at midnight"
    enhanced = service.inject_character_consistency_into_prompt(base_prompt, profile)

    assert "David" in enhanced
    assert "wireframe glasses" in enhanced
    assert "dark navy trench coat" in enhanced.lower()
    assert "9:16 aspect ratio" in enhanced
