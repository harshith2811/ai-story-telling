"""
Automated Tests for Subtitle Synchronization, ASS Karaoke Tags, and Telugu Font Support
"""

import tempfile
from pathlib import Path
from app.services.subtitle_engine.subtitle_service import SubtitleService


def test_word_timestamp_alignment():
    """Verify word-level timestamp generation and ordering."""
    service = SubtitleService()
    text = "Never underestimate the power of relentless effort and perseverance."
    timed_words = service._interpolate_word_timestamps(text, total_duration=5.0)

    assert len(timed_words) == len(text.split())
    # Ensure monotonic timing
    prev_end = 0.0
    for w in timed_words:
        assert w["start"] >= prev_end - 0.05
        assert w["end"] > w["start"]
        prev_end = w["end"]


def test_ass_subtitle_generation():
    """Verify ASS subtitle generation with Nirmala UI font and active word highlighting."""
    service = SubtitleService()
    timed_words = [
        {"word": "Never", "start": 0.2, "end": 0.6},
        {"word": "give", "start": 0.6, "end": 1.0},
        {"word": "up.", "start": 1.0, "end": 1.5},
    ]

    with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as tmp:
        out_path = Path(tmp.name)

    try:
        service.generate_ass_subtitles(timed_words, out_path, font_name="Nirmala UI")
        assert out_path.exists()
        content = out_path.read_text(encoding="utf-8")
        assert "ScriptType: v4.00+" in content
        assert "Nirmala UI" in content
        assert "Dialogue:" in content
        assert "\\c&H0020E5FF\\b1" in content  # Gold highlight tag
    finally:
        if out_path.exists():
            out_path.unlink()
