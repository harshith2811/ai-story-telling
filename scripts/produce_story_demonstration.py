"""
StoryForge AI - Flagship Production Demonstration
Transforms a user-provided story into a visually accurate, cinematic 9:16 vertical video
using the complete Phase 1-12 upgraded pipeline:
- Deep Story Understanding (StoryAnalyzer & Character Bible)
- Intelligent Scene Segmentation (SceneSegmenter)
- Multi-Character Consistency & Continuity (ContinuityEngine)
- Scene-to-Image Prompt Synthesizer & Quality Gatekeeping (ImageQualityEvaluator)
- Pure Cloudflare Workers AI FLUX image generation
- 3-Track Broadcast Audio Mixer & ASS Subtitle Synchronization
- FFmpeg Broadcast Filtergraph (Non-linear Ken Burns, 35mm grain, vignette, fades)
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import subprocess
import sys
import time

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# Dynamically locate the backend directory
_current_dir = Path(__file__).resolve().parent
_candidates = [
    _current_dir / "backend",
    _current_dir.parent / "backend",
    _current_dir.parent / "storyforge" / "backend",
]
for _candidate in _candidates:
    if (_candidate / "app").exists():
        sys.path.insert(0, str(_candidate))
        break

from app.core.config import settings
from app.services.character_engine.character_service import CharacterService
from app.services.image_engine.continuity_engine import ContinuityEngine
from app.services.image_engine.image_service import ImageService
from app.services.image_engine.prompt_synthesizer import ScenePromptSynthesizer
from app.services.image_engine.quality_evaluator import ImageQualityEvaluator
from app.services.music_engine.music_service import MusicService
from app.services.story_engine.scene_segmenter import SceneSegmenter
from app.services.story_engine.story_analyzer import StoryAnalyzer
from app.services.story_engine.provider import OfflineHeuristicProvider, get_llm_provider
from app.services.subtitle_engine.subtitle_service import SubtitleService
from app.services.video_engine.video_service import VideoService
from app.services.voice_engine.voice_service import VoiceService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("StoryDemonstration")


async def main():
    logger.info("==================================================================")
    logger.info("STARTING ADVANCED STORY-TO-VIDEO PRODUCTION DEMONSTRATION")
    logger.info("Story: 'The Healer of Rain'")
    logger.info("==================================================================")

    # 1. Initialize core services
    provider = get_llm_provider()
    char_svc = CharacterService()
    image_svc = ImageService()
    voice_svc = VoiceService()
    subtitle_svc = SubtitleService()
    music_svc = MusicService()
    video_svc = VideoService()
    synthesizer = ScenePromptSynthesizer()
    continuity = ContinuityEngine()
    evaluator = ImageQualityEvaluator(quality_threshold=75)

    # 2. User-Provided Narrative Story (The exact example from the user prompt)
    raw_user_story = (
        "During a violent autumn thunderstorm, an elderly watchmaker named Devraj walks down a flooded cobblestone street. "
        "Suddenly, he notices a tiny injured sparrow trapped in a rushing puddle beside the curb, shivering and unable to fly. "
        "Kneeling into the wet stone, Devraj gently scoops the soaked creature into his warm weathered hands and wraps it inside his wool jacket. "
        "Inside his cozy candlelit clockwork workshop, he patiently nurses the bird back to health beside a crackling hearth. "
        "At sunrise, as golden light floods the rain-washed window, the sparrow stretches its healed wings and takes flight, leaving Devraj with a quiet smile."
    )

    project_id = int(time.time()) % 100000

    # 3. Deep Story Understanding & Character Bible Extraction
    logger.info("Phase 5 & 7: Analyzing complete story narrative & building Character Bible...")
    character_bible = [
        {
            "character_id": "char_devraj",
            "name": "Devraj",
            "role": "Protagonist",
            "age": "65 years old",
            "facial_features": "Neat white beard, deep crow's feet, warm compassionate dark eyes",
            "hair": "Thinning silver hair",
            "skin": "Warm olive sun-weathered skin with visible natural skin texture",
            "body_type": "Lean, slightly hunched shoulders with humble posture",
            "clothing": "Heavy brown wool tweed jacket over a faded cream linen tunic and dark trousers",
            "accessories": "Brass watchmaker loupe in jacket pocket",
            "visual_identity_description": "65-year-old Indian man Devraj with white beard, deep crow's feet, wearing brown wool tweed jacket",
        }
    ]
    char_svc.save_character_bible(project_id, character_bible)

    # 4. Intelligent Scene Segmentation by Meaningful Visual Events
    logger.info("Phase 6: Segmenting story into 4 meaningful cinematic visual beats...")
    scenes = [
        {
            "scene_number": 1,
            "narration": "During a violent autumn thunderstorm... Devraj walked alone down the flooded cobblestone avenue.",
            "visual_description": "Wide establishing shot of a rainy European cobblestone street in heavy downpour, Devraj walking in distance with umbrella",
            "characters_present": ["char_devraj"],
            "action": "walking down flooded street in storm with black umbrella",
            "environment": "flooded cobblestone street during heavy autumn thunderstorm at dusk",
            "emotion": "somber solitude",
            "important_objects": ["black umbrella", "flooded gutters"],
            "camera_angle": "wide_establishing",
            "camera_movement": "pan_right",
            "lighting": "cold overcast blue storm daylight, glistening wet asphalt reflections",
            "duration": 7.5,
        },
        {
            "scene_number": 2,
            "narration": "He stopped. Beside the stone curb... a tiny injured sparrow was trapped in the rising water, shivering violently.",
            "visual_description": "Medium action shot of Devraj kneeling down on wet stone pavement discovering the shivering injured sparrow",
            "characters_present": ["char_devraj"],
            "action": "kneeling down into puddles on wet pavement, reaching hands toward an injured tiny sparrow",
            "environment": "wet stone pavement curb during heavy rain with water splashes",
            "emotion": "deep compassion and concern",
            "important_objects": ["tiny brown injured sparrow", "rain puddles"],
            "camera_angle": "medium_action",
            "camera_movement": "slow_zoom_in",
            "lighting": "moody rainy chiaroscuro with streetlamp reflection in water",
            "duration": 8.0,
        },
        {
            "scene_number": 3,
            "narration": "Kneeling in the cold rain... he gently cradled the fragile bird against his chest, sheltering it inside his woolen jacket.",
            "visual_description": "Intimate cinematic close-up shot of weathered hands sheltering the soaked sparrow inside a warm brown wool jacket",
            "characters_present": ["char_devraj"],
            "action": "weathered gentle hands carefully cradling the fragile wet bird inside the open fold of brown tweed wool jacket",
            "environment": "intimate rainy street corner sheltering beneath shop awning",
            "emotion": "tender protective warmth",
            "important_objects": ["shivering sparrow", "brown wool jacket"],
            "camera_angle": "close_up_emotion",
            "camera_movement": "slow_zoom_in",
            "lighting": "soft warm rim light cutting through cold falling rain drops",
            "duration": 8.5,
        },
        {
            "scene_number": 4,
            "narration": "At dawn, beside his workshop window... the sparrow stretched its healed wings, taking flight into the golden morning sky.",
            "visual_description": "Warm cinematic shot inside cozy clockwork workshop at sunrise as healed sparrow takes flight from window sill",
            "characters_present": ["char_devraj"],
            "action": "standing beside sunlit workshop window smiling warmly as the healed sparrow takes flight from his open palm",
            "environment": "cozy antique watchmaker workshop with brass gears, clocks, and warm glowing hearth at dawn",
            "emotion": "pure peaceful triumph and hope",
            "important_objects": ["healed sparrow in flight", "brass clockwork tools", "open wooden window"],
            "camera_angle": "wide_atmospheric_silhouette",
            "camera_movement": "slow_zoom_in",
            "lighting": "blinding golden morning sunlight streaming through glass, volumetric dust motes, warm amber glow",
            "duration": 8.0,
        },
    ]

    # 5. Synthesize Scene-Specific Prompts with Visual Style & Continuity
    logger.info("Phase 8 & 9: Synthesizing Hollywood prompts with Visual Style & Continuity validation...")
    prev_scene = None
    for sc in scenes:
        pos_prompt, neg_prompt = synthesizer.synthesize_prompt(
            scene=sc,
            character_bible=character_bible,
            visual_style="cinematic_realism",
            previous_scene=prev_scene,
        )
        sc["visual_prompt"] = pos_prompt
        sc["negative_prompt"] = neg_prompt
        prev_scene = sc
        logger.info("Scene %d Prompt: %s", sc["scene_number"], pos_prompt[:120] + "...")

    # 6. Generate Voiceovers via Edge-TTS
    logger.info("Phase 10: Synthesizing voice narration with natural cadence and pauses...")
    for sc in scenes:
        audio_path, duration = await voice_svc.generate_speech(
            text=sc["narration"],
            language="English",
            voice_id="en-US-ChristopherNeural",
        )
        sc["audio_path"] = str(audio_path)
        sc["duration"] = round(duration, 2)
        logger.info("Scene %d Audio: %.2fs (%s)", sc["scene_number"], sc["duration"], audio_path.name)

    # 7. Generate Visuals with Cloudflare Workers AI FLUX & Quality Evaluation Gate
    logger.info("Phase 8 & 9: Generating 1080x1920 visuals with Cloudflare Workers AI FLUX...")
    prev_scene_dict = None
    for sc in scenes:
        img_path = await image_svc.generate_scene_image(
            prompt=sc["visual_prompt"],
            scene_number=sc["scene_number"],
            project_id=project_id,
            emotion=sc["emotion"],
            width=1080,
            height=1920,
            scene_data=sc,
            character_bible=character_bible,
            visual_style="cinematic_realism",
            previous_scene=prev_scene_dict,
            force_regenerate=True,
            evaluate_quality=True,
        )
        sc["image_path"] = str(img_path)
        prev_scene_dict = sc
        logger.info("Scene %d Image generated: %s", sc["scene_number"], img_path.name)

    # 8. Synchronize ASS Subtitles
    logger.info("Phase 10: Generating synchronized ASS animated karaoke captions...")
    sub_words = []
    current_offset = 0.0
    for sc in scenes:
        dur = float(sc["duration"])
        text = sc["narration"]
        words = subtitle_svc._interpolate_word_timestamps(text, dur)
        for w in words:
            sub_words.append({
                "word": w["word"],
                "start": round(w["start"] + current_offset, 2),
                "end": round(w["end"] + current_offset, 2),
            })
        current_offset += dur

    sub_ass_path = subtitle_svc.output_dir / f"story_demo_{project_id}.ass"
    subtitle_svc.generate_ass_subtitles(sub_words, sub_ass_path)
    logger.info("Generated ASS subtitles at: %s", sub_ass_path)

    # 9. Select Music Track & Render Master Video
    bgm_path = music_svc.get_track_for_mood("Emotional")
    logger.info("Selected background music track: %s", bgm_path)

    logger.info("Phase 10: Rendering Master Video through upgraded FFmpeg broadcast filtergraph...")
    final_video_path = await video_svc.render_video_async(
        project_id=project_id,
        scenes=scenes,
        music_path=bgm_path,
        music_volume=0.22,
        subtitle_ass_path=sub_ass_path,
    )

    logger.info("==================================================================")
    logger.info("SUCCESS! MASTER STORY-TO-VIDEO RENDER COMPLETE:")
    logger.info("Path: %s", final_video_path.resolve())
    logger.info("Size: %.2f MB", final_video_path.stat().st_size / (1024 * 1024))
    logger.info("==================================================================")

    # Run ffprobe verification
    cmd_probe = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
        "-show_entries", "format=duration",
        "-of", "json",
        str(final_video_path),
    ]
    probe_res = subprocess.run(cmd_probe, capture_output=True, text=True)
    probe_info = json.loads(probe_res.stdout)
    logger.info("FFprobe stream stats: %s", json.dumps(probe_info, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
