from __future__ import annotations

from audiorepodigest.forecasting import ForecastEngine
from audiorepodigest.models import TrendAnalysis


def test_forecast_engine_marks_output_as_heuristic() -> None:
    analysis = TrendAnalysis(
        headline="The period leaned toward audio_ai work.",
        dominant_tags=["audio_ai", "speech", "developer_tooling"],
        repeated_keywords=["tts", "transcription", "realtime"],
        theme_counts={"audio_ai": 4, "speech": 3},
        segment_counts={"speech / voice AI": 3},
    )

    forecast = ForecastEngine().generate(analysis, [])
    assert "heuristic" in forecast.intro.lower()
    assert len(forecast.items) == 4
    assert "Directional estimate" in forecast.items[0].estimate
