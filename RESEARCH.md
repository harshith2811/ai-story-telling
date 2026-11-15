# StoryForge AI — Comprehensive Technology & Repository Research

## 1. Executive Summary

StoryForge AI is an end-to-end, free-first AI storytelling and viral vertical video production studio. It transforms a simple user prompt into an emotionally compelling, professionally voiced, visually consistent 9:16 vertical video for YouTube Shorts, Instagram Reels, and TikTok.

This document analyzes the four target reference repositories, evaluates the best open-source technologies for each pipeline stage, outlines license constraints, and details our hardware-adaptive architecture tailored for consumer-tier hardware (e.g., NVIDIA RTX 3050 4GB VRAM / CPU environments).

---

## 2. In-Depth Analysis of Required Repositories

### 1. `Chamanrajragu/purffle-shorts`
* **Repository URL:** [https://github.com/Chamanrajragu/purffle-shorts](https://github.com/Chamanrajragu/purffle-shorts)
* **License:** MIT License (Permissive)
* **Maintenance & Status:** Actively maintained through 2025–2026.
* **Key Architecture & Capabilities:**
  - Automated vertical short-form video generation pipeline.
  - Multi-LLM script generation support (OpenAI, Claude, Gemini, Ollama local).
  - Voice generation and word-synced animated captions.
  - Social media publishing hooks for YouTube and TikTok.
* **Hardware Requirements:** CPU-capable for audio and video assembly via FFmpeg; GPU optional for local LLM/image gen.
* **Role in StoryForge AI:** **Architectural Reference.** We adopt its clean linear stage-pipeline pattern (Prompt → Script → Narration → Subtitles → Assembly → Publishing) while expanding from basic clips to rich, emotionally nuanced storytelling with multi-hook intelligence and character consistency.

### 2. `qmmughal/texttovideo` (Frame)
* **Repository URL:** [https://github.com/qmmughal/texttovideo](https://github.com/qmmughal/texttovideo)
* **License:** MIT License (Permissive)
* **Maintenance & Status:** Maintained through late 2026.
* **Key Architecture & Capabilities:**
  - Local-first AI video studio designed for complete offline privacy.
  - Operates on CPU without requiring high-end GPUs (uses OpenVINO / CPU models).
  - Integrates Ollama, Piper TTS, ComfyUI, FastAPI backend, and modern UI.
  - Built-in local moderation filters via Ollama to prevent harmful content.
* **Hardware Requirements:** 8GB–16GB RAM, standard x86 CPU, optional GPU.
* **Role in StoryForge AI:** **Strong Reference & Component Pattern.** We adopt its privacy-preserving local-first philosophy, fallback mechanisms for resource-constrained hardware, and robust content safety evaluation.

### 3. `comfyanonymous/ComfyUI`
* **Repository URL:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
* **License:** GNU General Public License v3.0 (GPLv3 - Copyleft)
* **Maintenance & Status:** Industry standard; exceptionally active development with thousands of custom nodes.
* **Key Architecture & Capabilities:**
  - Node-based graph execution engine for Stable Diffusion 1.5, SDXL, and Flux.
  - Headless API mode (`/prompt`, `/history`, `/view`, WebSocket progress).
  - Modular support for IP-Adapter, ControlNet, and InstantID.
* **Hardware Requirements:** GPU with minimum 4GB VRAM (`--lowvram` flag) up to 24GB+ VRAM for Flux/SDXL.
* **Role in StoryForge AI:** **External Service via REST/WebSocket API.**
  > [!IMPORTANT]
  > Because ComfyUI is licensed under **GPLv3**, StoryForge AI communicates with ComfyUI strictly over HTTP/WebSocket network boundaries as an external client service. This preserves StoryForge AI's clean MIT/Apache licensing structure without copyleft contamination.

### 4. `FFmpeg/FFmpeg`
* **Repository URL:** [https://github.com/FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg)
* **License:** LGPL v2.1+ (default build) / GPL v2+ (when built with `--enable-gpl`)
* **Maintenance & Status:** Universal multimedia foundation across all operating systems.
* **Key Architecture & Capabilities:**
  - High-performance video filtering: `zoompan` (Ken Burns effect), `xfade` (cinematic transitions), `drawtext` / `subtitles` / ASS subtitle overlays.
  - Advanced audio filtergraphs: `amix`, `sidechaincompress` / dynamic volume ducking, and `loudnorm` (EBU R128 standard).
  - Hardware encoding acceleration (`h264_nvenc` for NVIDIA, `h264_amf` for AMD, `h264_qsv` for Intel, or `libx264` CPU fallback).
* **Role in StoryForge AI:** **Core Primary Rendering Engine.** All final composition is executed via direct FFmpeg filtergraphs for speed, determinism, and minimal memory overhead.

---

## 3. Technology Stack Evaluation & Selection

| Pipeline Stage | Primary Technology | Free/Local Fallback | Cloud/Paid Alternative (Optional) | License |
|---|---|---|---|---|
| **Local LLM Engine** | Ollama (`llama3.2:3b`, `mistral:7b`, `phi3:mini`) | Deterministic Rule-Based Story Generator & Heuristic Engine | OpenAI GPT-4o-mini, Anthropic Claude 3.5, Groq | MIT / Apache 2.0 |
| **TTS Narration** | Edge-TTS (Neural, zero cost, English & Telugu native) | Piper TTS (Offline CPU, ONNX) / Kokoro-82M | ElevenLabs API | Apache 2.0 / MIT |
| **Speech Alignment** | `faster-whisper` (CTranslate2 INT8, word-level timestamps) | Interpolated phoneme/word-rate sync algorithm | OpenAI Whisper API | MIT |
| **Image Generation** | ComfyUI API (SD 1.5 / SDXL Turbo / IP-Adapter) | Procedural Canvas Compositor with High-Aesthetic Typography & Ken Burns | Pollinations API, DALL-E 3, Fal.ai | Permissive API layer |
| **Character Consistency** | IP-Adapter FaceID via ComfyUI / Seed & Style Lock | Persistent visual description embedding & reference caching | Midjourney Persona (`--cref`) | Apache 2.0 |
| **Video Rendering** | FFmpeg filtergraphs (H.264, 1080x1920, 30fps) | FFmpeg software encoder (`libx264`) | Cloud video renderers | LGPL v2.1 |
| **Audio & Ducking** | FFmpeg `sidechaincompress` & `loudnorm` (EBU R128) | PyDub amplitude mixing | AudioCraft | LGPL / MIT |
| **Backend Framework** | FastAPI + SQLAlchemy + aiosqlite (SQLite) | In-memory / file-based persistence | PostgreSQL | MIT |
| **Frontend UI** | React + TypeScript + Tailwind CSS | Vanilla SPA dashboard fallback | N/A | MIT |
| **Publishing** | Official Google/YouTube Data API v3 OAuth2 | Manual MP4 & metadata export bundle | Zapier / Make | Apache 2.0 |

---

## 4. Hardware Optimization (RTX 3050 4GB & CPU Profile)

On consumer hardware with 4GB VRAM:
1. **Model Memory Footprint:**
   - LLMs: 3B–4B quantized models (e.g. `llama3.2:3b-instruct-q4_K_M`) fit comfortably inside 2.2GB VRAM or can be CPU-offloaded without blocking video encoding.
   - Images: SD 1.5 models with `--lowvram` run in ~2.5GB VRAM.
   - TTS: Edge-TTS and Piper run on CPU with near-zero VRAM usage.
   - Whisper: `faster-whisper` with `tiny` or `base` INT8 models consumes < 300MB RAM.
2. **Deterministic Fallbacks:**
   - When no local GPU or daemon is running, StoryForge AI seamlessly falls back to its offline heuristic engine and procedural canvas composer. The user is never blocked from generating valid vertical MP4 videos!

---

## 5. Third-Party Licenses & Attribution Strategy

- **MIT Licensed Repositories:** All code adapted or referenced from `purffle-shorts`, `texttovideo`, and `faster-whisper` carries original copyright headers and attribution notices.
- **LGPL/GPL (FFmpeg & ComfyUI):** We invoke FFmpeg as an external subprocess binary and ComfyUI as a decoupled HTTP REST microservice. No proprietary or MIT code is dynamically linked to GPL code.
- **TTS Licenses:** Edge-TTS utilizes the public Edge browser websocket API; Piper TTS ONNX models are MIT/Apache 2.0. Coqui TTS was rejected due to restrictive non-commercial licensing.
- **Audio Assets:** All included background music tracks are royalty-free and creative-commons/public-domain licensed with metadata credits embedded.
