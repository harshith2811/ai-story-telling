export interface Scene {
  id: number;
  project_id: number;
  scene_number: number;
  narration: string;
  emotion?: string;
  visual_prompt?: string;
  image_path?: string;
  audio_path?: string;
  duration?: number;
  camera_movement?: string;
  music_mood?: string;
}

export interface Character {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  visual_description?: string;
  reference_image_path?: string;
}

export interface HookEvaluation {
  overall_score: number;
  scores: {
    curiosity: number;
    emotional_impact: number;
    clarity: number;
    relevance: number;
    originality: number;
    immediate_attention: number;
  };
  strengths: string[];
  weaknesses: string[];
  improvement_suggestion: string;
}

export interface AlternativeHook {
  hook_text: string;
  hook_type: string;
  explanation: string;
}

export interface QualityAudit {
  quality_score: number;
  verdict: string;
  critique: {
    beginning_score: number;
    clarity_score: number;
    emotional_progression_score: number;
    ending_score: number;
    pacing_fit_score: number;
  };
  weak_sentences: string[];
  actionable_recommendations: string[];
}

export interface StoryMetadata {
  title: string;
  hook: string;
  story: string;
  moral: string;
  estimated_duration: number;
  alternative_hooks?: AlternativeHook[];
  hook_evaluation?: HookEvaluation;
  quality_audit?: QualityAudit;
}

export interface Project {
  id: number;
  title: string;
  topic: string;
  status: string;
  category?: string;
  language: string;
  duration_target: number;
  emotional_tone: string;
  audience: string;
  visual_style: string;
  narrator?: string;
  story_json?: string;
  created_at: string;
  updated_at: string;
  scenes: Scene[];
  characters: Character[];
}

export interface SystemDiagnostics {
  app_name: string;
  version: string;
  environment: Record<string, any>;
  services: {
    ffmpeg: { installed: boolean; version: string; status: string };
    llm_engine: { provider: string; ollama_online: boolean; status: string };
    voice_tts: { provider: string; available: boolean; telugu_support: boolean; status: string };
    speech_alignment: { provider: string; available: boolean; status: string };
    image_generation: { provider: string; comfyui_online: boolean; status: string };
    youtube_publishing: { configured: boolean; status: string };
  };
}

export interface AnalyticsScorecard {
  views: number;
  avg_view_duration: number;
  percentage_watched: number;
  retention_3s: number;
  completion_rate: number;
  likes: number;
  comments: number;
  shares: number;
  subscribers_gained: number;
  engagement_rate: number;
  subscriber_conversion_rate: number;
  performance_tier: string;
  recommendations: string[];
}
