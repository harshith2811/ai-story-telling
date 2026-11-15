"""
StoryForge Public API Harvester Engine
Ingests real-world anomalies, cosmic discoveries, and historical events from free public APIs
(listed in public-apis/public-apis) to autonomously generate high-retention vertical reels.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, Optional
import httpx

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

logger = logging.getLogger(__name__)


class PublicAPIHarvester:
    """Harvester for zero-key/free public APIs listed on github.com/public-apis/public-apis."""

    def __init__(self):
        self.headers = {
            "User-Agent": "StoryForgeEngine/2.0 (Autonomous Video Generator; https://github.com/storyforge)"
        }

    async def fetch_cosmic_anomaly(self) -> Dict[str, Any]:
        """Harvest cosmic mysteries from NASA APOD and NeoWs (Near Earth Object Web Service)."""
        logger.info("Fetching real cosmic anomaly from NASA Open Data API...")
        async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
            # 1. Try Near Earth Asteroid Flybys
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                neo_url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key=DEMO_KEY"
                res = await client.get(neo_url)
                if res.status_code == 200:
                    data = res.json()
                    neos = data.get("near_earth_objects", {}).get(today, [])
                    if neos:
                        # Find largest or hazardous object
                        sorted_neos = sorted(
                            neos,
                            key=lambda x: x.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0),
                            reverse=True,
                        )
                        target = sorted_neos[0]
                        name = target.get("name")
                        diameter_m = round(
                            target.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0)
                        )
                        close_data = target.get("close_approach_data", [{}])[0]
                        velocity_kmh = round(
                            float(close_data.get("relative_velocity", {}).get("kilometers_per_hour", 0))
                        )
                        miss_distance_km = round(
                            float(close_data.get("miss_distance", {}).get("kilometers", 0))
                        )
                        is_hazardous = target.get("is_potentially_hazardous_asteroid", False)

                        logger.info("Harvested asteroid anomaly: %s (diameter %dm)", name, diameter_m)
                        return {
                            "source": "NASA NeoWs",
                            "topic_type": "cosmic_hazard",
                            "title": f"The Phantom Titan: Asteroid {name}",
                            "summary": (
                                f"A colossal celestial object named Asteroid {name}, measuring {diameter_m} meters across "
                                f"— taller than a 100-story skyscraper — is hurtling past Earth today at {velocity_kmh:,} km/h, "
                                f"missing our atmosphere by {miss_distance_km:,} kilometers."
                            ),
                            "metadata": {
                                "diameter_meters": diameter_m,
                                "velocity_kmh": velocity_kmh,
                                "miss_distance_km": miss_distance_km,
                                "is_hazardous": is_hazardous,
                            },
                        }
            except Exception as exc:
                logger.warning("NASA NeoWs query failed, falling back to NASA APOD: %s", exc)

            # 2. Try NASA APOD (Astronomy Picture of the Day)
            try:
                apod_url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
                res = await client.get(apod_url)
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("title", "Cosmic Phenomenon")
                    explanation = data.get("explanation", "")
                    logger.info("Harvested NASA APOD discovery: %s", title)
                    return {
                        "source": "NASA APOD",
                        "topic_type": "deep_space_phenomenon",
                        "title": title,
                        "summary": explanation[:400] + "...",
                        "metadata": {
                            "date": data.get("date"),
                            "media_type": data.get("media_type"),
                        },
                    }
            except Exception as exc:
                logger.error("NASA APOD query failed: %s", exc)

        # Fallback offline cosmic anomaly
        return {
            "source": "NASA Deep Space Archive",
            "topic_type": "cosmic_mystery",
            "title": "The Wow! Signal of Sagittarius",
            "summary": "In 1977, the Big Ear radio telescope caught a 72-second narrowband signal from the constellation Sagittarius that matched every expected profile of an interstellar transmission.",
            "metadata": {"frequency": "1420 MHz", "duration_seconds": 72},
        }

    async def fetch_historical_anomaly(self) -> Dict[str, Any]:
        """Harvest dark historical anomalies and unsolved events from Wikimedia OnThisDay."""
        logger.info("Fetching real historical anomaly from Wikimedia API...")
        now = datetime.now()
        month = now.strftime("%m")
        day = now.strftime("%d")
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{month}/{day}"

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    events = data.get("selected", []) or data.get("events", [])
                    if events:
                        # Pick an intriguing event with historical weight
                        chosen = events[-1] if len(events) > 1 else events[0]
                        year = chosen.get("year", "Unknown Year")
                        text = chosen.get("text", "")
                        return {
                            "source": "Wikimedia On This Day",
                            "topic_type": "historical_anomaly",
                            "title": f"The Forgotten Event of {year}",
                            "summary": f"On this very date in the year {year}, history shifted in silence: {text}",
                            "metadata": {"year": year, "date": f"{month}-{day}"},
                        }
        except Exception as exc:
            logger.warning("Wikimedia query failed: %s", exc)

        return {
            "source": "Historical Archive",
            "topic_type": "unsolved_historical_mystery",
            "title": "The Ghost Vessel of 1872",
            "summary": "In December 1872, the Mary Celeste was found floating in the Atlantic with full sails, intact cargo, and warm food on the table—yet every soul aboard had vanished without a trace.",
            "metadata": {"vessel": "Mary Celeste", "year": 1872},
        }
