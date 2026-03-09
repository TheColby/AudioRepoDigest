from __future__ import annotations

from collections.abc import Iterable

from audiorepodigest.classification import RepositoryClassifier
from audiorepodigest.config import DigestSettings
from audiorepodigest.discovery import RepositoryDiscoverer
from audiorepodigest.forecasting import ForecastEngine
from audiorepodigest.github_client import GitHubClient
from audiorepodigest.models import CategoryKey, DateRange, PipelineResult, RepositoryCandidate
from audiorepodigest.ranking import RankingEngine
from audiorepodigest.reporting import ReportComposer, ReportRenderer, build_section
from audiorepodigest.trends import TrendAnalyzer
from audiorepodigest.utils.dates import resolve_period


class AudioRepoDigestPipeline:
    """End-to-end digest generation pipeline."""

    def __init__(self, settings: DigestSettings, github_client: GitHubClient | None = None) -> None:
        self.settings = settings
        self._owns_client = github_client is None
        self.github_client = github_client or GitHubClient(settings.github_token)
        classifier = RepositoryClassifier(
            allowlist_topics=settings.allowlist_topics,
            blocklist_terms=settings.blocklist_terms,
        )
        self.discoverer = RepositoryDiscoverer(self.github_client, classifier, settings)
        self.ranking = RankingEngine()
        self.trend_analyzer = TrendAnalyzer()
        self.forecaster = ForecastEngine()
        self.report_composer = ReportComposer()
        self.report_renderer = ReportRenderer()

    def close(self) -> None:
        if self._owns_client:
            self.github_client.close()

    def __enter__(self) -> AudioRepoDigestPipeline:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.close()

    def build_digest(
        self,
        *,
        period: DateRange | None = None,
        categories: Iterable[CategoryKey] | None = None,
    ) -> PipelineResult:
        selected_categories = list(
            categories or (CategoryKey.TOP_AUDIO, CategoryKey.TOP_NEW, CategoryKey.TOP_AUDIO_AI)
        )
        effective_period = period or resolve_period(
            frequency=self.settings.report_frequency,
            timezone=self.settings.report_timezone,
            lookback_days=self.settings.report_lookback_days,
        )
        discovery = self.discoverer.discover(effective_period)

        sections = []
        selected_names: set[str] = set()

        if CategoryKey.TOP_AUDIO in selected_categories:
            top_audio = self.ranking.rank_top_audio(
                discovery.candidates,
                effective_period,
                self.settings.top_n_main,
            )
            sections.append(build_section(CategoryKey.TOP_AUDIO, top_audio))
            selected_names.update(item.candidate.full_name for item in top_audio)

        if CategoryKey.TOP_NEW in selected_categories:
            top_new = self.ranking.rank_top_new(
                discovery.candidates,
                effective_period,
                self.settings.top_n_new,
            )
            sections.append(build_section(CategoryKey.TOP_NEW, top_new))
            selected_names.update(item.candidate.full_name for item in top_new)

        if CategoryKey.TOP_AUDIO_AI in selected_categories:
            top_audio_ai = self.ranking.rank_top_audio_ai(
                discovery.candidates,
                effective_period,
                self.settings.top_n_audio_ai,
            )
            sections.append(build_section(CategoryKey.TOP_AUDIO_AI, top_audio_ai))
            selected_names.update(item.candidate.full_name for item in top_audio_ai)

        if self.settings.include_honorable_mentions:
            honorable_exclude = (
                selected_names if self.settings.suppress_honorable_mention_duplicates else set()
            )
            honorable_mentions = self.ranking.select_honorable_mentions(
                discovery.candidates,
                effective_period,
                exclude=honorable_exclude,
                limit=min(5, max(3, self.settings.top_n_new)),
            )
            if honorable_mentions:
                sections.append(build_section(CategoryKey.HONORABLE_MENTIONS, honorable_mentions))

        trend_analysis = (
            self.trend_analyzer.analyze(sections, discovery.candidates)
            if self.settings.include_trend_analysis
            else None
        )
        forecast_section = (
            self.forecaster.generate(trend_analysis, sections)
            if self.settings.include_forecasts and trend_analysis is not None
            else None
        )

        report = self.report_composer.compose(
            settings=self.settings,
            period=effective_period,
            period_label=effective_period.label,
            discovery=discovery,
            sections=sections,
            trend_analysis=trend_analysis,
            forecast_section=forecast_section,
        )
        render_bundle = self.report_renderer.render(report, self.settings)
        return PipelineResult(report=report, render_bundle=render_bundle, discovery=discovery)

    def collect_candidates(self, *, period: DateRange | None = None) -> list[RepositoryCandidate]:
        effective_period = period or resolve_period(
            frequency=self.settings.report_frequency,
            timezone=self.settings.report_timezone,
            lookback_days=self.settings.report_lookback_days,
        )
        return self.discoverer.discover(effective_period).candidates

    def explain_repository(
        self,
        full_name: str,
        *,
        period: DateRange | None = None,
    ) -> dict[CategoryKey, object]:
        effective_period = period or resolve_period(
            frequency=self.settings.report_frequency,
            timezone=self.settings.report_timezone,
            lookback_days=self.settings.report_lookback_days,
        )
        repository = self.github_client.get_repository(full_name)
        classifier = self.discoverer.classifier
        repository.classification = classifier.classify(repository)
        return self.ranking.explain_scores(repository, effective_period)
