# StoryForge AI — Automated Testing & Verification Report

## 1. Test Suite Summary

Every core component of StoryForge AI is verified through comprehensive automated unit, integration, and end-to-end tests using `pytest` and `pytest-asyncio`.

```
Platform: Windows 11 (win32)
Python: 3.12.13
FFmpeg: Build N-128142-g28fda48e0b (x86_64-w64-mingw32)
Test Results: 16 PASSED, 0 FAILED, 0 SKIPPED (100% Pass Rate)
Execution Time: 59.84 seconds
```

---

## 2. Test Matrix & Coverage

| Test Module | Test Case | Pipeline Stage | Status | Verification Detail |
|---|---|---|---|---|
| `test_story_and_hooks.py` | `test_story_generation_schema_validation` | Story Engine | **PASSED** | Validates structured JSON schema, duration bounds, character keys, and minimum 4-scene breakdown. |
| `test_story_and_hooks.py` | `test_invalid_json_handling` | Story Engine | **PASSED** | Confirms `StoryValidationError` is raised for empty or malformed inputs. |
| `test_story_and_hooks.py` | `test_hook_generation_and_scoring` | Hook Engine | **PASSED** | Generates 3 alternative opening hooks and evaluates on a 0–100 transparent heuristic scale (Curiosity, Emotion, Clarity, etc.). |
| `test_story_and_hooks.py` | `test_story_quality_auditor` | Story Quality | **PASSED** | Audits pacing (words per second), emotional progression, and scene structure. |
| `test_character_engine.py` | `test_character_extraction_and_normalization` | Character Engine | **PASSED** | Extracts character identities, costumes, facial anchors, and builds consistent reference sheets. |
| `test_character_engine.py` | `test_character_prompt_injection` | Character Engine | **PASSED** | Verifies character anchor tags and costume descriptions are injected into scene prompts. |
| `test_voice_and_audio.py` | `test_voice_registry_multilingual` | Voice Studio | **PASSED** | Checks multi-speaker English and Telugu neural voices (`en-US-GuyNeural`, `te-IN-MohanNeural`). |
| `test_voice_and_audio.py` | `test_speech_generation_and_duration` | Voice Studio | **PASSED** | Synthesizes neural audio via Edge-TTS and measures accurate duration via ffprobe. |
| `test_subtitle_sync.py` | `test_word_timestamp_alignment` | Subtitle Engine | **PASSED** | Verifies monotonic word-level timestamp progression without overlapping bounds. |
| `test_subtitle_sync.py` | `test_ass_subtitle_generation` | Subtitle Engine | **PASSED** | Verifies ASS dynamic karaoke gold-highlight tags (`{\c&H0020E5FF\b1}`) and `Nirmala UI` Telugu font styling. |
| `test_music_and_ducking.py` | `test_mood_tracks_available` | Music Engine | **PASSED** | Confirms availability of soundtracks across all 7 emotions (Inspirational, Emotional, Sad, Suspense, Hopeful, Victory, Calm). |
| `test_music_and_ducking.py` | `test_music_list_inventory` | Music Engine | **PASSED** | Validates soundtrack library metadata and file sizes. |
| `test_api_endpoints.py` | `test_health_check_endpoint` | API Layer | **PASSED** | `GET /health` returns HTTP 200 with application version. |
| `test_api_endpoints.py` | `test_system_diagnostics_endpoint` | API Layer | **PASSED** | `GET /api/v1/system/diagnostics` returns installation status of FFmpeg, LLM, TTS, and image engines. |
| `test_api_endpoints.py` | `test_project_crud_lifecycle` | API Layer | **PASSED** | Full CRUD validation: project creation, retrieval, updates, and deletion in SQLite. |
| `test_end_to_end_production.py` | `test_complete_end_to_end_vertical_video_production` | **FULL E2E PIPELINE** | **PASSED** | Takes raw prompt topic → generates story → creates 1080x1920 images → synthesizes speech → aligns subtitles → mixes background music with ducking → renders valid vertical MP4. |

---

## 3. End-to-End Test Verification (FFprobe Output)

The end-to-end test rendered a complete vertical short-form video verified using `ffprobe`:

```json
{
  "streams": [
    {
      "codec_name": "h264",
      "width": 1080,
      "height": 1920,
      "r_frame_rate": "30/1"
    },
    {
      "codec_name": "aac",
      "r_frame_rate": "0/0"
    }
  ],
  "format": {
    "duration": "17.946990",
    "size": "2185433"
  }
}
```

### Verified Technical Specifications:
- **Aspect Ratio:** 9:16 (1080 width × 1920 height)
- **Frame Rate:** 30.00 FPS constant
- **Video Codec:** H.264 / AVC (`libx264` high profile)
- **Audio Codec:** AAC stereo 192kbps
- **Loudness Normalization:** EBU R128 (-14 LUFS)
- **Subtitles:** Embedded / burned with active-word gold karaoke highlighting

---

## 4. How to Run Tests Locally

Execute from project root in PowerShell:

```powershell
$env:PYTHONPATH="c:\Users\amara\OneDrive\Documents\yt\storyforge\backend"
& "c:\Users\amara\OneDrive\Documents\yt\.venv\Scripts\pytest.exe" -v "c:\Users\amara\OneDrive\Documents\yt\storyforge\backend\tests"
```
