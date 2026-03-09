from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from audiorepodigest.classification import RepositoryClassifier
from audiorepodigest.config import DigestSettings
from audiorepodigest.forecasting import ForecastEngine
from audiorepodigest.models import CategoryKey, DateRange, DiscoveryResult, RepositoryCandidate
from audiorepodigest.ranking import RankingEngine
from audiorepodigest.reporting import ReportComposer, ReportRenderer, build_section
from audiorepodigest.trends import TrendAnalyzer

TEST_CLASSIFIER = RepositoryClassifier()


def make_repository(
    *,
    full_name: str = "acme/audio-dsp",
    description: str = "Audio DSP toolkit for synthesis and analysis.",
    topics: list[str] | None = None,
    language: str | None = "Python",
    stars: int = 250,
    forks: int = 30,
    watchers: int = 20,
    issues: int = 5,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    pushed_at: datetime | None = None,
) -> RepositoryCandidate:
    topics = topics or ["audio", "dsp", "synthesis"]
    created_at = created_at or datetime(2025, 1, 1, tzinfo=UTC)
    updated_at = updated_at or datetime(2026, 3, 8, tzinfo=UTC)
    pushed_at = pushed_at or datetime(2026, 3, 8, tzinfo=UTC)
    owner, name = full_name.split("/", 1)
    repository = RepositoryCandidate(
        id=abs(hash(full_name)) % 100000,
        full_name=full_name,
        name=name,
        owner=owner,
        html_url=f"https://github.com/{full_name}",
        description=description,
        topics=topics,
        language=language,
        created_at=created_at,
        updated_at=updated_at,
        pushed_at=pushed_at,
        stargazers_count=stars,
        forks_count=forks,
        watchers_count=watchers,
        open_issues_count=issues,
        source_queries=["test"],
        raw_payload={},
    )
    repository.classification = TEST_CLASSIFIER.classify(repository)
    return repository


@pytest.fixture()
def period() -> DateRange:
    return DateRange(
        start=datetime(2026, 3, 2, tzinfo=UTC),
        end=datetime(2026, 3, 9, tzinfo=UTC),
        label="2026-03-02 to 2026-03-08",
    )


@pytest.fixture()
def settings(tmp_path) -> DigestSettings:
    return DigestSettings.model_validate(
        {
            "github_token": "test-token",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "sender@example.com",
            "smtp_password": "secret",
            "smtp_from": "AudioRepoDigest <sender@example.com>",
            "smtp_use_starttls": True,
            "smtp_use_ssl": False,
            "report_recipient_email": "colbyleider@gmail.com",
            "report_recipient_name": "Colby Leider",
            "report_frequency": "weekly",
            "report_timezone": "America/New_York",
            "top_n_main": 10,
            "top_n_new": 5,
            "top_n_audio_ai": 5,
            "include_honorable_mentions": True,
            "include_trend_analysis": True,
            "include_forecasts": True,
            "max_candidates_to_scan": 100,
            "github_search_window_days": 21,
            "log_level": "INFO",
            "email_subject_prefix": "[AudioRepoDigest]",
            "output_html_path": tmp_path / "digest.html",
            "output_markdown_path": tmp_path / "digest.md",
            "output_json_path": tmp_path / "digest.json",
        }
    )


@pytest.fixture()
def rendered_report_bundle(settings: DigestSettings, period: DateRange):
    ranking = RankingEngine()
    main_repo = make_repository(
        full_name="acme/audio-dsp",
        description="Audio DSP toolkit for synthesis, spectral analysis, and plugins.",
        topics=["audio", "dsp", "plugins", "synthesis"],
        stars=1400,
        forks=150,
        issues=12,
    )
    ai_repo = make_repository(
        full_name="acme/neural-audio-lab",
        description="Text-to-audio diffusion and speech generation toolkit for voice AI.",
        topics=["audio", "speech", "machine-learning", "generative-audio"],
        stars=2100,
        forks=220,
        watchers=90,
        issues=14,
    )
    new_repo = make_repository(
        full_name="acme/new-audio-note",
        description="Fresh MIDI and notation workflow for music software teams.",
        topics=["music", "midi", "notation"],
        stars=180,
        forks=12,
        created_at=period.start + timedelta(days=1),
        updated_at=period.end - timedelta(days=1),
        pushed_at=period.end - timedelta(days=1),
    )

    sections = [
        build_section(
            CategoryKey.TOP_AUDIO, ranking.rank_top_audio([main_repo, ai_repo], period, 5)
        ),
        build_section(CategoryKey.TOP_NEW, ranking.rank_top_new([new_repo, main_repo], period, 5)),
        build_section(
            CategoryKey.TOP_AUDIO_AI, ranking.rank_top_audio_ai([ai_repo, main_repo], period, 5)
        ),
    ]
    trend_analysis = TrendAnalyzer().analyze(sections, [main_repo, ai_repo, new_repo])
    forecast = ForecastEngine().generate(trend_analysis, sections)
    discovery = DiscoveryResult(
        candidates=[main_repo, ai_repo, new_repo],
        query_count=5,
        raw_candidate_count=12,
        relevant_candidate_count=3,
    )
    report = ReportComposer().compose(
        settings=settings,
        period=period,
        period_label=period.label,
        discovery=discovery,
        sections=sections,
        trend_analysis=trend_analysis,
        forecast_section=forecast,
    )
    bundle = ReportRenderer().render(report, settings)
    return report, bundle
