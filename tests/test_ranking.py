from __future__ import annotations

from datetime import timedelta

from audiorepodigest.ranking import RankingEngine

from .conftest import make_repository


def test_top_audio_ranking_prefers_established_active_repo(period) -> None:
    established = make_repository(
        full_name="acme/audio-core",
        description="Audio DSP engine for plugins and synthesis.",
        topics=["audio", "dsp", "plugins", "synthesis"],
        stars=3200,
        forks=310,
        pushed_at=period.end - timedelta(days=1),
    )
    lower_signal = make_repository(
        full_name="acme/small-audio-tool",
        description="Audio utility for waveform conversion.",
        topics=["audio"],
        stars=120,
        forks=5,
        pushed_at=period.end - timedelta(days=3),
    )

    ranked = RankingEngine().rank_top_audio([lower_signal, established], period, 5)
    assert ranked[0].candidate.full_name == "acme/audio-core"


def test_top_new_only_includes_repositories_created_within_period(period) -> None:
    new_repo = make_repository(
        full_name="acme/new-music-tool",
        description="New MIDI sequencing environment for music software teams.",
        topics=["music", "midi", "sequencer"],
        created_at=period.start + timedelta(days=2),
        updated_at=period.end - timedelta(days=1),
        pushed_at=period.end - timedelta(days=1),
        stars=250,
    )
    old_repo = make_repository(
        full_name="acme/old-music-tool",
        description="Legacy MIDI sequencing environment.",
        topics=["music", "midi"],
        created_at=period.start - timedelta(days=60),
    )

    ranked = RankingEngine().rank_top_new([old_repo, new_repo], period, 5)
    assert [entry.candidate.full_name for entry in ranked] == ["acme/new-music-tool"]
    assert "created during the reporting window" in ranked[0].why_included


def test_random_audio_selection_respects_exclusions(period) -> None:
    repositories = [
        make_repository(
            full_name=f"acme/audio-random-{index}",
            description="Audio repository candidate for random weekly section.",
            topics=["audio", "dsp"],
            stars=50 + index,
        )
        for index in range(8)
    ]
    excluded = {"acme/audio-random-1", "acme/audio-random-2"}

    ranked = RankingEngine().select_random_audio(
        repositories,
        period,
        exclude=excluded,
        limit=5,
    )
    assert len(ranked) == 5
    assert all(item.candidate.full_name not in excluded for item in ranked)
