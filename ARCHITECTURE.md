# StoryForge AI — System Architecture & Technical Specification

## 1. System Overview

**StoryForge AI** is a production-grade, modular content creation platform that automates the transformation of a simple text prompt into a viral vertical video (1080×1920, 9:16) for YouTube Shorts, Instagram Reels, and TikTok.

### End-to-End Workflow

```mermaid
flowchart TD
    A["User Prompt / Topic"] --> B["AI Story Engine\n(Multi-Style Script Generation)"]
    B --> C["Hook Intelligence Engine\n(3+ Hooks & Heuristic 0-100 Scoring)"]
    C --> D["Story Quality Evaluator\n(Coherence, Pacing & Duration Checks)"]
    D --> E["Storyboard Engine\n(Scene Breakdown, Emotions, Camera Directives)"]
    E --> F["Character Engine\n(Character Extraction & Consistency Profiles)"]
    E --> G["Image Generation Engine\n(ComfyUI / Diffusers / Fallback Compositor)"]
    E --> H["Voice Studio Engine\n(Edge-TTS / Piper: EN & TE Voices)"]
    H --> I["Subtitle & Sync Engine\n(faster-whisper / Word-Level Timestamps)"]
    E --> J["Background Music Engine\n(Mood-Matched Royalty-Free Tracks)"]
    G --> K["Video Production Engine\n(FFmpeg: Ken Burns, Xfade, Ducking, Loudnorm)"]
    H --> K
    I --> K
    J --> K
    K --> L["Final 1080x1920 MP4 Video Preview"]
    L --> M["YouTube Publishing Engine\n(OAuth2, Metadata Optimization, Approval Gate)"]
    M --> N["Performance Analytics & Feedback Engine\n(3s Retention, AVD, Optimization Loop)"]
```

---

## 2. Directory Structure

```
storyforge/
├── assets/
│   ├── characters/           # Character reference sheets & images
│   ├── audio/                # Voiceovers & sound effects
│   ├── music/                # Royalty-free music library categorized by mood
│   └── fonts/                # Fonts with Telugu Unicode support (Nirmala UI / Noto Sans)
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints & WebSocket routes
│   │   │   ├── routes/       # projects, stories, scenes, images, audio, renders, youtube, analytics
│   │   │   └── websockets/   # real-time progress broadcast
│   │   ├── core/             # Configuration, logging, events
│   │   ├── database/         # SQLite async engine, session factory, base metadata
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # Modular domain services
│   │   │   ├── story_engine/
│   │   │   ├── hook_engine/
│   │   │   ├── storyboard_engine/
│   │   │   ├── character_engine/
│   │   │   ├── image_engine/
│   │   │   ├── voice_engine/
│   │   │   ├── subtitle_engine/
│   │   │   ├── music_engine/
│   │   │   ├── video_engine/
│   │   │   ├── analytics_engine/
│   │   │   └── youtube_engine/
│   │   ├── storage/          # Local file storage handlers
│   │   └── workers/          # Background task queue & job executors
│   ├── tests/                # Automated unit and integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components (Header, Sidebar, Player, Cards)
│   │   ├── pages/            # Dashboard, CreateStory, StoryEditor, Storyboard, VoiceStudio, VideoEditor, Analytics, Settings
│   │   ├── services/         # Axios/Fetch API client & WebSocket client
│   │   └── types/            # TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.js
├── outputs/
│   ├── projects/             # Project state dumps
│   ├── videos/               # Final rendered MP4 files
│   ├── subtitles/            # Synchronized SRT & ASS files
│   └── thumbnails/           # Auto-generated YouTube thumbnails
├── RESEARCH.md
├── ARCHITECTURE.md
├── TESTING.md
└── README.md
```

---

## 3. Database Schema

The persistence layer uses SQLite with SQLAlchemy AsyncSession.

```mermaid
erDiagram
    PROJECT ||--o{ SCENE : contains
    PROJECT ||--o{ CHARACTER : features
    PROJECT ||--o{ VIDEO_RENDER : produces
    PROJECT ||--o{ VIDEO_ANALYTICS : tracks
    PROJECT ||--o{ GENERATION_HISTORY : logs

    PROJECT {
        int id PK
        string title
        string topic
        string status
        string category
        string language
        float duration_target
        string emotional_tone
        string audience
        string visual_style
        string narrator
        text story_json
        datetime created_at
        datetime updated_at
    }

    SCENE {
        int id PK
        int project_id FK
        int scene_number
        text narration
        string emotion
        text visual_prompt
        string image_path
        string audio_path
        float duration
        string camera_movement
        string music_mood
    }

    CHARACTER {
        int id PK
        int project_id FK
        string name
        string role
        text visual_description
        string reference_image_path
        string costume
        string facial_features
    }

    VIDEO_RENDER {
        int id PK
        int project_id FK
        string output_path
        string resolution
        int fps
        float duration
        int file_size_bytes
        string render_status
        float progress
        text error_message
        datetime started_at
        datetime completed_at
    }

    VIDEO_ANALYTICS {
        int id PK
        int project_id FK
        string platform
        string video_id
        int views
        float avg_view_duration
        float retention_3s
        float completion_rate
        int likes
        int comments
        int shares
        int subscribers_gained
        text recommendations
        datetime last_synced_at
    }

    GENERATION_HISTORY {
        int id PK
        int project_id FK
        string stage
        text input_payload
        text output_payload
        int duration_ms
        string status
        datetime created_at
    }
```

---

## 4. Subtitle & Multi-Language Specification (English & Telugu)

Subtitles use Advanced SubStation Alpha (`.ass`) or FFmpeg `drawtext` with:
- **Font:** `Nirmala UI` or `Noto Sans Telugu` with complete Unicode glyph support.
- **Dynamic Word Highlighting:** As each word is spoken, its color shifts from muted white (`#FFFFFF`) to vibrant amber-gold (`#FFD700`) with a dark outline (`#000000`).
- **Safe Margins:** Vertical placement is fixed at 75% height to avoid covering TikTok/Shorts UI buttons (likes, profile, share).

---

## 5. Video Composition Engine (FFmpeg Pipeline)

Each scene is composited using a robust FFmpeg filtergraph:
1. **Dynamic Ken Burns:**
   - Zoom in: `zoompan=z='min(zoom+0.0015,1.25)':d=duration*fps:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30`
   - Pan left-to-right or right-to-left based on scene camera metadata.
2. **Audio Mixing & Ducking:**
   - Background music track is looped and attenuated by 18dB whenever speech audio is active using `sidechaincompress` or dynamic volume envelopes.
3. **Audio Normalization:**
   - Master audio is normalized to EBU R128 (-14 LUFS for YouTube Shorts).
