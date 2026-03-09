from __future__ import annotations

from audiorepodigest.models import CategoryKey
from audiorepodigest.ranking import RankingEngine
from audiorepodigest.reporting import build_section
from audiorepodigest.trends import TrendAnalyzer

from .conftest import make_repository


def test_trend_analyzer_highlights_underrepresented_segments(period) -> None:
    ranking = RankingEngine()
    selected_ai = make_repository(
        full_name="acme/voice-stack",
        description="Speech recognition and voice AI toolkit for audio inference.",
        topics=["audio", "speech", "machine-learning"],
        stars=2000,
        forks=180,
    )
    selected_dsp = make_repository(
        full_name="acme/dsp-stack",
        description="FFT, filters, and audio DSP tooling.",
        topics=["audio", "dsp"],
        stars=900,
        forks=60,
    )
    plugin_candidates = [
        make_repository(
            full_name=f"acme/plugin-{index}",
            description="CLAP and VST plugin development utilities.",
            topics=["audio", "plugin", "clap", "vst"],
            stars=200 + index,
        )
        for index in range(4)
    ]

    sections = [
        build_section(
            CategoryKey.TOP_AUDIO_AI, ranking.rank_top_audio_ai([selected_ai], period, 5)
        ),
        build_section(CategoryKey.TOP_AUDIO, ranking.rank_top_audio([selected_dsp], period, 5)),
    ]
    analysis = TrendAnalyzer().analyze(sections, [selected_ai, selected_dsp, *plugin_candidates])
    assert analysis.headline
    assert "plugins" in analysis.underrepresented_segments
