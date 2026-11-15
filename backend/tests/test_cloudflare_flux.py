"""
Test Cloudflare Workers AI FLUX-1-Schnell Integration
"""

import base64
import io
from pathlib import Path
from unittest.mock import AsyncMock, patch
from PIL import Image
import pytest

from app.core.config import settings
from app.services.image_engine.image_service import ImageService


@pytest.mark.asyncio
async def test_cloudflare_flux_graceful_fallback_without_keys(tmp_path, monkeypatch):
    """When Cloudflare credentials are missing, it falls back gracefully without raising errors."""
    svc = ImageService(output_dir=tmp_path)
    monkeypatch.setattr(settings, "CLOUDFLARE_ACCOUNT_ID", "")
    monkeypatch.setattr(settings, "CLOUDFLARE_API_TOKEN", "")
    with patch("os.environ.get", return_value=None):
        res = await svc._try_cloudflare_flux("test prompt", tmp_path / "test.png")
        assert res is None


@pytest.mark.asyncio
async def test_cloudflare_flux_synthesis_with_mock_response(tmp_path, monkeypatch):
    """When Cloudflare returns an image stream, it is fitted cleanly to 1080x1920."""
    import httpx
    svc = ImageService(output_dir=tmp_path)

    # Create dummy 512x512 image bytes
    dummy_im = Image.new("RGB", (512, 512), color=(200, 100, 50))
    buf = io.BytesIO()
    dummy_im.save(buf, "PNG")
    raw_bytes = buf.getvalue()

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "image/png"}
    mock_resp.content = raw_bytes

    dest_file = tmp_path / "cf_flux_test.png"

    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "mock_acc_123")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "mock_tok_456")

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
        res = await svc._try_cloudflare_flux("test prompt", dest_file)
        assert res is not None
        assert res.exists()
        saved_im = Image.open(res)
        assert saved_im.size == (1080, 1920)
