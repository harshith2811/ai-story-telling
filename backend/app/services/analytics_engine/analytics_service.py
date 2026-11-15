"""
StoryForge AI - Analytics & Viral Optimization Engine

Tracks performance metrics (3s retention, AVD, completion rate, likes/shares),
provides comparative cohort analysis, and generates actionable storytelling
recommendations based on empirical performance data.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Calculates engagement analytics and generates data-driven content recommendations."""

    def calculate_video_scorecard(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Process raw platform metrics into standardized retention and engagement indicators."""
        views = max(1, int(metrics.get("views", 0)))
        duration = max(1.0, float(metrics.get("video_duration", 60.0)))
        avg_view_duration = float(metrics.get("avg_view_duration", 0.0))
        retention_3s = float(metrics.get("retention_3s", 0.0))
        likes = int(metrics.get("likes", 0))
        comments = int(metrics.get("comments", 0))
        shares = int(metrics.get("shares", 0))
        subscribers_gained = int(metrics.get("subscribers_gained", 0))

        percentage_watched = min(100.0, (avg_view_duration / duration) * 100.0)
        engagement_rate = ((likes + comments * 2 + shares * 3) / views) * 100.0
        subscriber_conversion_rate = (subscribers_gained / views) * 100.0

        # Heuristic performance tier (internal comparative metric)
        if retention_3s >= 75.0 and percentage_watched >= 70.0:
            performance_tier = "Top 5% (Viral Potential)"
        elif retention_3s >= 60.0 and percentage_watched >= 50.0:
            performance_tier = "Above Average"
        elif retention_3s >= 45.0:
            performance_tier = "Average"
        else:
            performance_tier = "Needs Hook Optimization"

        recommendations = self.generate_recommendations(
            retention_3s, percentage_watched, engagement_rate, duration
        )

        return {
            "views": views,
            "avg_view_duration": round(avg_view_duration, 1),
            "percentage_watched": round(percentage_watched, 1),
            "retention_3s": round(retention_3s, 1),
            "completion_rate": round(float(metrics.get("completion_rate", percentage_watched * 0.8)), 1),
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "subscribers_gained": subscribers_gained,
            "engagement_rate": round(engagement_rate, 2),
            "subscriber_conversion_rate": round(subscriber_conversion_rate, 2),
            "performance_tier": performance_tier,
            "recommendations": recommendations,
        }

    def generate_recommendations(
        self,
        retention_3s: float,
        percentage_watched: float,
        engagement_rate: float,
        duration: float,
    ) -> list[str]:
        """Synthesize concrete editorial guidelines based on performance signals."""
        recs: list[str] = []

        if retention_3s < 60.0:
            recs.append(
                "Hook Alert: Drop-off in the first 3 seconds is significant (<60%). "
                "Use curiosity or conflict hooks that cut straight to the action without intro pauses."
            )
        else:
            recs.append(
                "Strong Opening: Initial 3-second retention is healthy. "
                "The opening visual and hook phrasing successfully prevented scrolling."
            )

        if percentage_watched < 50.0:
            recs.append(
                f"Mid-Story Pacing: Viewers are leaving before the conclusion. "
                f"Consider tightening scene durations (target 40-50s instead of {int(duration)}s) "
                "and increasing camera movement variety."
            )
        else:
            recs.append(
                "Compelling Narrative Arc: High completion percentage indicates strong emotional progression."
            )

        if engagement_rate < 3.0:
            recs.append(
                "Call-to-Action: Comments and shares are modest. End with an open philosophical question "
                "in the final 5 seconds to spark viewer opinions in comments."
            )

        return recs
