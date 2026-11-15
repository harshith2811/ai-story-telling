"""
Test Public API Harvester Engine
"""

import pytest
from app.services.harvest_engine.public_api_harvester import PublicAPIHarvester


@pytest.mark.asyncio
async def test_harvest_cosmic_anomaly():
    harvester = PublicAPIHarvester()
    res = await harvester.fetch_cosmic_anomaly()
    assert "source" in res
    assert "title" in res
    assert "summary" in res
    assert len(res["summary"]) > 20


@pytest.mark.asyncio
async def test_harvest_historical_anomaly():
    harvester = PublicAPIHarvester()
    res = await harvester.fetch_historical_anomaly()
    assert "source" in res
    assert "title" in res
    assert "summary" in res
    assert len(res["summary"]) > 20
