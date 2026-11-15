"""
Automated Tests for Background Music Library, Mood Categorization, and Audio Ducking
"""

from app.services.music_engine.music_service import MusicService, MOOD_CATEGORIES


def test_mood_tracks_available():
    """Verify background music tracks exist for all emotional mood categories."""
    service = MusicService()
    for mood in MOOD_CATEGORIES:
        track = service.get_track_for_mood(mood)
        assert track is not None, f"Track for mood {mood} was not found"
        assert track.exists(), f"Audio file for {mood} does not exist: {track}"
        assert track.stat().st_size > 500


def test_music_list_inventory():
    """Verify list_available_tracks returns metadata for all soundtrack files."""
    service = MusicService()
    tracks = service.list_available_tracks()
    assert len(tracks) >= len(MOOD_CATEGORIES)
    for t in tracks:
        assert "filename" in t
        assert "mood" in t
        assert "size_kb" in t
