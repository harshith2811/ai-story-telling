import { Project, SystemDiagnostics, AnalyticsScorecard } from '../types';

const API_BASE = '/api/v1';

export const api = {
  async getDiagnostics(): Promise<SystemDiagnostics> {
    const res = await fetch(`${API_BASE}/system/diagnostics`);
    if (!res.ok) throw new Error('Failed to fetch diagnostics');
    return res.json();
  },

  async listProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects/`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProject(id: number): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  },

  async generateStory(params: {
    topic: string;
    category: string;
    language: string;
    duration: number;
    emotional_tone: string;
    audience: string;
    visual_style: string;
  }): Promise<Project> {
    const res = await fetch(`${API_BASE}/stories/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Failed to generate story');
    return res.json();
  },

  async evaluateHook(hook_text: string, topic: string) {
    const res = await fetch(`${API_BASE}/stories/hooks/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hook_text, topic }),
    });
    return res.json();
  },

  async rewriteSection(current_text: string, story_context: string, revision_goal: string) {
    const res = await fetch(`${API_BASE}/stories/rewrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_text, story_context, revision_goal }),
    });
    return res.json();
  },

  async updateScene(sceneId: number, data: Partial<any>) {
    const res = await fetch(`${API_BASE}/scenes/${sceneId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async generateSceneImage(sceneId: number) {
    const res = await fetch(`${API_BASE}/images/generate/${sceneId}`, {
      method: 'POST',
    });
    return res.json();
  },

  async listVoices(language?: string) {
    const url = language ? `${API_BASE}/audio/voices?language=${language}` : `${API_BASE}/audio/voices`;
    const res = await fetch(url);
    return res.json();
  },

  async previewVoice(voice_id: string, language: string, sample_text?: string, speed: number = 1.0) {
    const res = await fetch(`${API_BASE}/audio/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ voice_id, language, sample_text, speed }),
    });
    return res.json();
  },

  async startRender(projectId: number) {
    const res = await fetch(`${API_BASE}/renders/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, fps: 30, format: 'mp4' }),
    });
    return res.json();
  },

  async getRenderStatus(projectId: number) {
    const res = await fetch(`${API_BASE}/renders/status/${projectId}`);
    return res.json();
  },

  async getAnalytics(projectId: number): Promise<AnalyticsScorecard> {
    const res = await fetch(`${API_BASE}/analytics/project/${projectId}`);
    return res.json();
  },

  async getYouTubeMetadata(projectId: number) {
    const res = await fetch(`${API_BASE}/youtube/metadata/${projectId}`);
    return res.json();
  },

  async publishYouTube(projectId: number, userApproved: boolean, customTitle?: string) {
    const res = await fetch(`${API_BASE}/youtube/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        user_approved: userApproved,
        custom_title: customTitle,
      }),
    });
    return res.json();
  },
};
