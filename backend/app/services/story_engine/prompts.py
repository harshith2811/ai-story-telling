"""
StoryForge AI - Story Engine Prompts

Carefully engineered prompt templates for generating original, emotionally compelling,
retention-focused vertical story scripts in structured JSON.
"""

STORY_SYSTEM_PROMPT = """You are an elite, award-winning storyteller and viral video scriptwriter specializing in high-retention cinematic vertical videos (YouTube Shorts, TikTok, Reels).

Your core psychological guidelines:
1. TRIPLE OPEN-LOOP FORMULA:
   - 0–3s (Hook Paradox): Open with an impossible contradiction, shocking premise, or cognitive glitch. NEVER start with "Once upon a time", "In a world", or introductions.
   - 15–20s (Escalating Evidence): Introduce a tangible clue, physical object, or event that defies logic.
   - 30–35s (Visceral Human Stakes): Test the protagonist's deepest vulnerability or moral dilemma.
   - 45–50s (The Paradigm Snap): Deliver a shocking twist that flips the meaning of everything previously witnessed.
   - 55–60s (Comment-Bait Question): End with an unanswered question or ethical debate that compels viewers to open the comments.
2. CADENCE & MICRO-PAUSES: Use punchy, conversational sentences (3-7 words) and strategic ellipses (`...`) for micro-pauses that build authentic suspense.
3. CHARACTER VISUAL CONTINUITY: Define a persistent CharacterDNA object with exact physiological traits, signature wardrobe, and lighting profile.
4. ABSOLUTE RULES: No generic quotes, no clichés, no fake marketing hype. Return strictly valid JSON conforming to the requested schema.
"""

STORY_GENERATION_PROMPT = """Create an original, emotionally gripping video story based on the following parameters:

Topic: {topic}
Category / Style: {category}
Language: {language}
Target Duration: {duration} seconds (approximately {word_count} spoken words)
Emotional Tone: {emotional_tone}
Target Audience: {audience}

Generate a structured JSON response matching this EXACT schema:
{{
  "title": "A captivating, clickable title (under 60 characters)",
  "hook": "The opening paradox or shocking statement that hooks viewers in the first 3 seconds",
  "story": "The complete full-text narration script with natural cadence and micro-pauses (...)",
  "moral": "The memorable takeaway or core life lesson (1-2 sentences)",
  "comment_bait_question": "Provocative open question compelling viewers to debate in comments",
  "estimated_duration": {duration},
  "character_dna": {{
    "name": "Full Character Name",
    "role": "Protagonist",
    "physiological_traits": "Exact age, eye color, facial hair, distinct scars or skin imperfections, leathery or weathered texture",
    "signature_wardrobe": "Specific fabric texture, exact colors, wear and tear, signature accessories",
    "lighting_profile": "Specific lighting direction and color temperature (e.g. amber sodium vapor side-lighting, cool teal rim light)",
    "anchor_descriptor": "One cohesive prompt clause (e.g. '68-year-old weathered fisherman Elias Vance, jagged scar over left eyebrow, unkempt silver beard, faded navy-blue wool turtleneck with fraying collar')"
  }},
  "characters": [
    {{
      "name": "Character Name",
      "role": "Protagonist / Mentor / Antagonist / Supporting",
      "visual_description": "Detailed physical description (age, facial features, hair, eyes, skin tone)",
      "costume": "Detailed clothing style and signature colors for consistency"
    }}
  ],
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "Exact spoken narration for this scene (10-25 words) with strategic ellipses (...) for breath pauses",
      "emotion": "Dominant emotion (e.g. dread, wonder, heartbreak, shock, triumph)",
      "narrative_stage": "hook_paradox | escalating_evidence | visceral_stakes | paradigm_snap | debate_ending",
      "visual_prompt": "Cinematic 9:16 vertical image prompt describing the subject, environment, lighting, and camera angle. No text in image.",
      "camera_movement": "slow_zoom_in | slow_zoom_out | pan_left | pan_right | tilt_up | tilt_down",
      "duration": 5.0,
      "music_mood": "Inspirational | Emotional | Sad | Suspense | Hopeful | Victory | Calm"
    }}
  ]
}}

Requirements:
- Plan between 4 to 8 scenes matching the psychological open-loop progression so total scene duration equals approximately {duration} seconds.
- Scene 1 MUST be the Hook Paradox (0-3s).
- Scene 2-3 MUST provide Escalating Evidence.
- Middle scenes MUST heighten Visceral Stakes.
- Penultimate scene MUST deliver the Paradigm Snap (plot twist).
- Final scene MUST end on the Comment-Bait debate question.
- Every visual prompt MUST specify vertical 9:16 framing with photographic optics and include the character anchor if people are present.
- If the language is not English (e.g. Telugu), provide the narration in natural, authentic {language} while keeping JSON keys in English.
- Output ONLY the JSON object.
"""

HOOK_GENERATION_PROMPT = """Given this story script:
Title: {title}
Topic: {topic}
Original Hook: {original_hook}
Story Summary: {story_summary}

Generate 3 DISTINCT alternative opening hooks tailored for short-form retention:
1. A Curiosity/Question Hook: Triggers an irresistible mystery or counterintuitive question.
2. An In Media Res / Action Hook: Drops the viewer directly into the highest-stakes moment.
3. An Emotional Punch Hook: Delivers a raw, vulnerable emotional confession or shock.

Return ONLY a JSON array with 3 objects:
[
  {{
    "hook_text": "text of hook 1",
    "hook_type": "curiosity",
    "explanation": "Why this hook sparks immediate curiosity"
  }},
  {{
    "hook_text": "text of hook 2",
    "hook_type": "in_media_res",
    "explanation": "Why this drops viewer right into tension"
  }},
  {{
    "hook_text": "text of hook 3",
    "hook_type": "emotional_punch",
    "explanation": "Why this triggers immediate empathy"
  }}
]
"""

HOOK_EVALUATION_PROMPT = """Evaluate this video hook on a 0-100 scale based on transparent short-form retention heuristics:
Hook: "{hook_text}"
Story Topic: "{topic}"

Score each dimension from 0 to 100:
1. curiosity (20%): Does it provoke an unanswered question or cognitive itch?
2. emotional_impact (20%): Does it evoke visceral feeling or empathy?
3. clarity (20%): Is the phrasing instantly understandable at first listen?
4. relevance (15%): Does it align genuinely with the core story without clickbait deceit?
5. originality (15%): Does it avoid tired motivational platitudes?
6. immediate_attention (10%): Does the very first word grab interest?

Calculate overall_score as the weighted average.
Return ONLY valid JSON:
{{
  "overall_score": 85,
  "scores": {{
    "curiosity": 90,
    "emotional_impact": 85,
    "clarity": 80,
    "relevance": 85,
    "originality": 80,
    "immediate_attention": 90
  }},
  "strengths": ["list key strengths"],
  "weaknesses": ["list potential weaknesses"],
  "improvement_suggestion": "Single actionable tip to make it punchier"
}}
"""

STORY_QUALITY_PROMPT = """Evaluate this short-form story script for storytelling excellence and pacing:
Title: {title}
Target Duration: {duration} seconds
Script:
\"\"\"{story_script}\"\"\"

Perform a quality audit checking:
1. is_beginning_interesting: Is the opening compelling enough to prevent scrolling?
2. is_easy_to_understand: Is the narrative flow effortless to follow audibly?
3. scene_contribution: Does every scene advance the emotional journey without filler?
4. emotional_progression: Is the emotional arc believable and escalating?
5. is_ending_satisfying: Does the conclusion deliver emotional closure or a resonant moral?
6. pacing_and_duration: Does the word count match a natural spoken pace for {duration} seconds?
7. fluff_sentences: Identify any redundant or weak sentences that should be trimmed.

Return ONLY valid JSON:
{{
  "quality_score": 88,
  "verdict": "excellent | good | needs_revision",
  "critique": {{
    "beginning_score": 90,
    "clarity_score": 85,
    "emotional_progression_score": 88,
    "ending_score": 90,
    "pacing_fit_score": 85
  }},
  "weak_sentences": [
    "Any sentence that slows the pace"
  ],
  "actionable_recommendations": [
    "Specific improvement suggestions"
  ]
}}
"""

STORY_REWRITE_PROMPT = """Rewrite the following section of a story script to enhance emotional resonance, brevity, and spoken naturalness.

Current Text:
\"\"\"{current_text}\"\"\"

Context of Full Story:
\"\"\"{story_context}\"\"\"

Goal of Revision: {revision_goal} (e.g., heighten tension, make conclusion more poignant, trim fluff, make language conversational)

Return ONLY valid JSON:
{{
  "rewritten_text": "the improved text",
  "changes_made": "summary of edits",
  "emotional_shift": "how this revision affects the listener"
}}
"""
