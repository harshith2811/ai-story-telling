"""
Automated Tests for FastAPI Endpoints, Diagnostics & CRUD Operations
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_check_endpoint():
    """Verify /health returns healthy status."""
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"


def test_system_diagnostics_endpoint():
    """Verify /api/v1/system/diagnostics returns complete service health matrix."""
    with TestClient(app) as client:
        res = client.get("/api/v1/system/diagnostics")
        assert res.status_code == 200
        data = res.json()
        assert "services" in data
        assert "ffmpeg" in data["services"]
        assert "voice_tts" in data["services"]
        assert "speech_alignment" in data["services"]
        assert data["services"]["ffmpeg"]["installed"] is True


def test_project_crud_lifecycle():
    """Verify project creation, retrieval, and updates."""
    with TestClient(app) as client:
        # Create
        create_res = client.post("/api/v1/projects/", json={
            "title": "Automated Test Project",
            "topic": "Testing project lifecycle",
            "language": "English",
            "duration_target": 60.0,
            "emotional_tone": "determination",
            "audience": "general",
            "visual_style": "cinematic"
        })
        assert create_res.status_code == 201
        proj = create_res.json()
        proj_id = proj["id"]

        # Get
        get_res = client.get(f"/api/v1/projects/{proj_id}")
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Automated Test Project"

        # Update
        patch_res = client.patch(f"/api/v1/projects/{proj_id}", json={
            "title": "Updated Test Project Title"
        })
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == "Updated Test Project Title"

        # Delete
        del_res = client.delete(f"/api/v1/projects/{proj_id}")
        assert del_res.status_code == 204


def test_audio_and_soundtrack_endpoints():
    """Verify /api/v1/audio/music, /preview, and /voices endpoints."""
    with TestClient(app) as client:
        # Voices list
        v_res = client.get("/api/v1/audio/voices")
        assert v_res.status_code == 200
        voices = v_res.json()
        assert len(voices) >= 6

        # Music library
        m_res = client.get("/api/v1/audio/music")
        assert m_res.status_code == 200
        tracks = m_res.json()
        assert len(tracks) >= 7

        # Music preview
        prev_res = client.get("/api/v1/audio/music/preview/Inspirational")
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        assert "audio_url" in prev_data
        assert "inspirational" in prev_data["filename"].lower()
