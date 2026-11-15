"""
Complete End-to-End Production Pipeline Test

Takes a sample topic, generates a multi-scene story, creates images,
generates voiceovers, builds dynamic subtitles, mixes music, and renders
a valid 1080x1920 30FPS vertical MP4 video verified via ffprobe.
"""

import json
from pathlib import Path
import subprocess
import pytest

from app.services.story_engine.provider import OfflineHeuristicProvider
from app.services.story_engine import StoryEngine
from app.services.image_engine.image_service import ImageService
from app.services.voice_engine.voice_service import VoiceService
from app.services.subtitle_engine.subtitle_service import SubtitleService
from app.services.music_engine.music_service import MusicService
from app.services.video_engine.video_service import VideoService


@pytest.mark.asyncio
async def test_complete_end_to_end_vertical_video_production(tmp_path):
    """End-to-End pipeline verification: Topic -> Story -> Visuals -> Voice -> Subtitles -> MP4."""
    # 1. Generate Story
    provider = OfflineHeuristicProvider()
    engine = StoryEngine(provider=provider)
    story = await engine.generate_story({
        "topic": "The boy who built a windmill from scrap metal",
        "category": "inspirational",
        "language": "English",
        "duration": 15,  # Compact duration for rapid test execution
        "emotional_tone": "determination",
        "audience": "general",
    })

    assert len(story["scenes"]) >= 2
    test_scenes = story["scenes"][:2]  # Test with 2 scenes for fast deterministic rendering

    # 2. Generate Scene Images
    image_service = ImageService(output_dir=tmp_path / "images")
    for sc in test_scenes:
        img_path = await image_service.generate_scene_image(
            prompt=sc["visual_prompt"],
            scene_number=sc["scene_number"],
            project_id=999,
            emotion=sc.get("emotion", "Inspirational"),
            width=1080,
            height=1920,
        )
        assert img_path.exists()
        sc["image_path"] = str(img_path)

    # 3. Generate Scene Voice Narration
    voice_service = VoiceService(output_dir=tmp_path / "audio")
    for sc in test_scenes:
        audio_path, duration = await voice_service.generate_speech(
            text=sc["narration"],
            language="English",
        )
        assert audio_path.exists()
        sc["audio_path"] = str(audio_path)
        sc["duration"] = round(duration, 1)

    # 4. Generate Synchronized Subtitles
    subtitle_service = SubtitleService(output_dir=tmp_path / "subtitles")
    full_text = " ".join(s["narration"] for s in test_scenes)
    total_dur = sum(s["duration"] for s in test_scenes)
    timed_words = subtitle_service._interpolate_word_timestamps(full_text, total_dur)

    sub_ass_path = tmp_path / "subtitles" / "e2e_subtitles.ass"
    subtitle_service.generate_ass_subtitles(timed_words, sub_ass_path)
    assert sub_ass_path.exists()

    # 5. Background Music & Ducking
    music_service = MusicService(music_dir=tmp_path / "music")
    bgm_track = music_service.get_track_for_mood("Inspirational")
    assert bgm_track is not None and bgm_track.exists()

    # 6. Full FFmpeg Video Assembly
    video_service = VideoService(renders_dir=tmp_path / "renders")
    output_mp4 = await video_service.render_video_async(
        project_id=999,
        scenes=test_scenes,
        music_path=bgm_track,
        music_volume=0.15,
        subtitle_ass_path=sub_ass_path,
    )

    # 7. Comprehensive ffprobe validation
    assert output_mp4.exists(), f"Rendered video does not exist: {output_mp4}"
    assert output_mp4.stat().st_size > 100000, "Rendered video file is abnormally small"

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
        "-show_entries", "format=duration",
        "-of", "json",
        str(output_mp4),
    ]
    probe_res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    probe_data = json.loads(probe_res.stdout)

    video_streams = [s for s in probe_data["streams"] if s["codec_name"] == "h264"]
    audio_streams = [s for s in probe_data["streams"] if s["codec_name"] == "aac"]

    assert len(video_streams) == 1, "Expected exactly 1 H.264 video stream"
    assert len(audio_streams) == 1, "Expected exactly 1 AAC audio stream"

    v_stream = video_streams[0]
    assert v_stream["width"] == 1080, f"Expected width 1080, got {v_stream['width']}"
    assert v_stream["height"] == 1920, f"Expected height 1920, got {v_stream['height']}"
    assert v_stream["r_frame_rate"] == "30/1", f"Expected 30 FPS, got {v_stream['r_frame_rate']}"

    duration = float(probe_data["format"]["duration"])
    assert duration > 2.0, f"Video duration too short: {duration}s"
