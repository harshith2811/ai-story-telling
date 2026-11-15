"""
StoryForge AI - Subtitle & Speech Synchronization Engine

Extracts word-level timestamps, formats dynamic highlighted captions,
and supports Telugu Unicode fonts (Nirmala UI) and English in ASS and SRT formats.
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SubtitleService:
    """Synchronizes narration audio with text and renders animated ASS/SRT subtitles."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or (Path(settings.BASE_DIR) / settings.STORAGE_DIR / "outputs" / "subtitles")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._whisper_model = None

    def _get_whisper_model(self):
        """Lazy loader for faster-whisper model."""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info("Initializing faster-whisper (tiny model, CPU INT8)...")
                self._whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            except Exception as exc:
                logger.warning("Could not initialize faster-whisper model: %s", exc)
                self._whisper_model = False
        return self._whisper_model

    def align_audio_with_text(
        self, audio_path: Path, script_text: str, total_duration: float
    ) -> list[dict[str, Any]]:
        """Extract word-level timestamps using Whisper alignment or precise interpolation."""
        model = self._get_whisper_model()

        if model and audio_path.exists() and audio_path.stat().st_size > 1000:
            try:
                segments, info = model.transcribe(
                    str(audio_path),
                    word_timestamps=True,
                    language=None,
                )
                words_list: list[dict[str, Any]] = []
                for segment in segments:
                    if segment.words:
                        for w in segment.words:
                            clean_w = w.word.strip()
                            if clean_w:
                                words_list.append({
                                    "word": clean_w,
                                    "start": round(w.start, 2),
                                    "end": round(w.end, 2),
                                })
                if len(words_list) >= 3:
                    logger.info("Whisper extracted %d word timestamps.", len(words_list))
                    return words_list
            except Exception as exc:
                logger.warning("Whisper transcription failed (%s); using interpolation.", exc)

        # Fallback: High-precision phonetic duration interpolation
        return self._interpolate_word_timestamps(script_text, total_duration)

    def _interpolate_word_timestamps(
        self, script_text: str, total_duration: float
    ) -> list[dict[str, Any]]:
        """Algorithmic word timing calculation based on syllable/character weights."""
        raw_words = [w for w in re.split(r"\s+", script_text.strip()) if w]
        if not raw_words:
            return []

        # Weigh words by character count to approximate spoken length
        weights = [max(2, len(w)) for w in raw_words]
        total_weight = sum(weights)

        # Leave small pause at start and end
        start_buffer = 0.2
        end_buffer = 0.2
        usable_time = max(1.0, total_duration - start_buffer - end_buffer)

        current_time = start_buffer
        timed_words: list[dict[str, Any]] = []

        for idx, (word, weight) in enumerate(zip(raw_words, weights)):
            duration = (weight / total_weight) * usable_time
            end_time = current_time + duration
            timed_words.append({
                "word": word,
                "start": round(current_time, 2),
                "end": round(end_time, 2),
            })
            current_time = end_time

        return timed_words

    def generate_ass_subtitles(
        self,
        timed_words: list[dict[str, Any]],
        output_path: Path,
        words_per_line: int = 4,
        font_name: str = "Nirmala UI",
        font_size: int = 52,
    ) -> Path:
        """Create an ASS subtitle file with dynamic active-word gold highlighting.
        
        Nirmala UI is the standard Windows font supporting English and Telugu Unicode.
        """
        # Group words into short dynamic phrases (3 to 5 words for Shorts readability)
        phrases: list[list[dict[str, Any]]] = []
        current_chunk: list[dict[str, Any]] = []

        for w in timed_words:
            current_chunk.append(w)
            if len(current_chunk) >= words_per_line or w["word"].endswith((".", "!", "?", ",", "।")):
                phrases.append(current_chunk)
                current_chunk = []
        if current_chunk:
            phrases.append(current_chunk)

        ass_header = f"""[Script Info]
Title: StoryForge Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,40,40,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for phrase in phrases:
            if not phrase:
                continue
            phrase_start = phrase[0]["start"]
            phrase_end = phrase[-1]["end"]

            # For each word in the phrase, create a momentary event where that word is highlighted in Gold (&H0000D7FF)
            for idx, target_word in enumerate(phrase):
                w_start_str = self._format_ass_time(target_word["start"])
                w_end_str = self._format_ass_time(target_word["end"])

                # Assemble line with target_word highlighted
                line_parts = []
                for other_idx, other_word in enumerate(phrase):
                    if other_idx == idx:
                        # Highlighted word (vibrant golden-yellow)
                        line_parts.append(f"{{\\c&H0020E5FF\\b1}}{other_word['word']}{{\\c&H00FFFFFF\\b0}}")
                    else:
                        line_parts.append(other_word["word"])

                text_payload = " ".join(line_parts)
                events.append(f"Dialogue: 0,{w_start_str},{w_end_str},Default,,0,0,0,,{text_payload}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

        logger.info("Exported ASS subtitle file: %s (%d events)", output_path, len(events))
        return output_path

    def generate_srt_subtitles(
        self, timed_words: list[dict[str, Any]], output_path: Path, words_per_chunk: int = 5
    ) -> Path:
        """Create standard SRT subtitles for YouTube / social video platforms."""
        chunks = [timed_words[i : i + words_per_chunk] for i in range(0, len(timed_words), words_per_chunk)]
        lines = []

        for idx, chunk in enumerate(chunks, start=1):
            start_time = self._format_srt_time(chunk[0]["start"])
            end_time = self._format_srt_time(chunk[-1]["end"])
            text = " ".join(w["word"] for w in chunk)

            lines.append(f"{idx}\n{start_time} --> {end_time}\n{text}\n")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_path

    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """Format seconds to ASS time string (H:MM:SS.cs)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds to SRT time string (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        if millis >= 1000:
            millis = 999
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
