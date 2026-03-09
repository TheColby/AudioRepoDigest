from __future__ import annotations

import math
from datetime import datetime

from audiorepodigest.models import (
    CategoryKey,
    DateRange,
    RankedRepository,
    RepositoryCandidate,
    ScoreBreakdown,
)


def _log_scale(value: int, cap: int) -> float:
    if value <= 0:
        return 0.0
    return min(math.log1p(value) / math.log1p(cap), 1.0)


def _recency_score(timestamp: datetime, period: DateRange) -> float:
    age_days = max(0.0, (period.end - timestamp).total_seconds() / 86_400)
    return max(0.0, 1.0 - (age_days / (period.days + 3)))


def _created_within_period(repository: RepositoryCandidate, period: DateRange) -> bool:
    return period.start <= repository.created_at < period.end


class RankingEngine:
    """Applies deterministic ranking heuristics for each report section."""

    def score_top_audio(self, repository: RepositoryCandidate, period: DateRange) -> ScoreBreakdown:
        classification = repository.classification
        if classification is None:
            raise ValueError("Repository must be classified before scoring.")

        components = {
            "relevance": classification.confidence * 32.0,
            "star_traction": _log_scale(repository.stargazers_count, 8_000) * 18.0,
            "fork_traction": _log_scale(repository.forks_count, 1_500) * 10.0,
            "watcher_traction": _log_scale(repository.watchers_count, 750) * 4.0,
            "push_recency": _recency_score(repository.pushed_at, period) * 18.0,
            "update_recency": _recency_score(repository.updated_at, period) * 8.0,
            "issue_surface": min(repository.open_issues_count, 40) / 40 * 4.0,
            "baseline_popularity": _log_scale(repository.stargazers_count, 250) * 6.0,
        }
        total = round(sum(components.values()), 2)
        explanation = (
            "Strong overall audio relevance combined with recent repository activity and "
            "meaningful baseline traction."
        )
        return ScoreBreakdown(
            category=CategoryKey.TOP_AUDIO,
            total_score=total,
            components={key: round(value, 2) for key, value in components.items()},
            explanation=explanation,
        )

    def score_top_new(self, repository: RepositoryCandidate, period: DateRange) -> ScoreBreakdown:
        classification = repository.classification
        if classification is None:
            raise ValueError("Repository must be classified before scoring.")

        age_days = max(1.0, (period.end - repository.created_at).total_seconds() / 86_400)
        velocity = (repository.stargazers_count + (2 * repository.forks_count)) / age_days
        components = {
            "novelty": 28.0 if _created_within_period(repository, period) else 0.0,
            "relevance": classification.confidence * 24.0,
            "early_star_traction": _log_scale(repository.stargazers_count, 1_500) * 22.0,
            "early_fork_traction": _log_scale(repository.forks_count, 250) * 12.0,
            "velocity": min(velocity / 40.0, 1.0) * 18.0,
            "sustained_activity": _recency_score(repository.pushed_at, period) * 10.0,
        }
        total = round(sum(components.values()), 2)
        explanation = (
            "Created inside the reporting window with enough early traction and ongoing activity "
            "to merit follow-up."
        )
        return ScoreBreakdown(
            category=CategoryKey.TOP_NEW,
            total_score=total,
            components={key: round(value, 2) for key, value in components.items()},
            explanation=explanation,
        )

    def score_top_audio_ai(
        self, repository: RepositoryCandidate, period: DateRange
    ) -> ScoreBreakdown:
        classification = repository.classification
        if classification is None:
            raise ValueError("Repository must be classified before scoring.")

        distinctive_ai_terms = len(
            {
                term
                for term in classification.matched_terms
                if term
                in {
                    "text-to-audio",
                    "text to audio",
                    "tts",
                    "asr",
                    "transcription",
                    "source separation",
                    "diffusion",
                    "voice conversion",
                    "speaker diarization",
                    "music generation",
                }
            }
        )
        components = {
            "audio_ai_relevance": classification.audio_ai_confidence * 35.0,
            "overall_relevance": classification.confidence * 10.0,
            "traction": (
                _log_scale(repository.stargazers_count, 6_000) * 18.0
                + _log_scale(repository.forks_count, 1_200) * 8.0
            ),
            "recent_activity": _recency_score(repository.pushed_at, period) * 18.0,
            "distinctiveness": min(distinctive_ai_terms / 5.0, 1.0) * 9.0,
            "novelty": (8.0 if _created_within_period(repository, period) else 0.0),
        }
        total = round(sum(components.values()), 2)
        explanation = (
            "High audio-AI specificity, solid momentum, and enough technical distinctiveness to "
            "stand out from generic model wrappers."
        )
        return ScoreBreakdown(
            category=CategoryKey.TOP_AUDIO_AI,
            total_score=total,
            components={key: round(value, 2) for key, value in components.items()},
            explanation=explanation,
        )

    def explain_scores(
        self,
        repository: RepositoryCandidate,
        period: DateRange,
    ) -> dict[CategoryKey, ScoreBreakdown]:
        return {
            CategoryKey.TOP_AUDIO: self.score_top_audio(repository, period),
            CategoryKey.TOP_NEW: self.score_top_new(repository, period),
            CategoryKey.TOP_AUDIO_AI: self.score_top_audio_ai(repository, period),
        }

    def rank_top_audio(
        self,
        repositories: list[RepositoryCandidate],
        period: DateRange,
        limit: int,
    ) -> list[RankedRepository]:
        eligible = [
            repository
            for repository in repositories
            if repository.classification
            and repository.classification.is_relevant
            and not repository.archived
            and not repository.fork
            and repository.created_at < period.start
        ]
        scored = sorted(
            ((repository, self.score_top_audio(repository, period)) for repository in eligible),
            key=lambda item: item[1].total_score,
            reverse=True,
        )
        return self._to_ranked(scored[:limit], CategoryKey.TOP_AUDIO, period)

    def rank_top_new(
        self,
        repositories: list[RepositoryCandidate],
        period: DateRange,
        limit: int,
    ) -> list[RankedRepository]:
        eligible = [
            repository
            for repository in repositories
            if repository.classification
            and repository.classification.is_relevant
            and not repository.archived
            and not repository.fork
            and _created_within_period(repository, period)
        ]
        scored = sorted(
            ((repository, self.score_top_new(repository, period)) for repository in eligible),
            key=lambda item: item[1].total_score,
            reverse=True,
        )
        return self._to_ranked(scored[:limit], CategoryKey.TOP_NEW, period)

    def rank_top_audio_ai(
        self,
        repositories: list[RepositoryCandidate],
        period: DateRange,
        limit: int,
    ) -> list[RankedRepository]:
        eligible = [
            repository
            for repository in repositories
            if repository.classification
            and repository.classification.is_relevant
            and repository.classification.audio_ai_confidence >= 0.35
            and not repository.archived
            and not repository.fork
        ]
        scored = sorted(
            ((repository, self.score_top_audio_ai(repository, period)) for repository in eligible),
            key=lambda item: item[1].total_score,
            reverse=True,
        )
        return self._to_ranked(scored[:limit], CategoryKey.TOP_AUDIO_AI, period)

    def select_honorable_mentions(
        self,
        repositories: list[RepositoryCandidate],
        period: DateRange,
        *,
        exclude: set[str],
        limit: int = 5,
    ) -> list[RankedRepository]:
        eligible = [
            repository
            for repository in repositories
            if repository.full_name not in exclude
            and repository.classification
            and repository.classification.is_relevant
            and not repository.archived
            and not repository.fork
        ]
        scored = sorted(
            ((repository, self.score_top_audio(repository, period)) for repository in eligible),
            key=lambda item: item[1].total_score,
            reverse=True,
        )
        return self._to_ranked(scored[:limit], CategoryKey.HONORABLE_MENTIONS, period)

    def _to_ranked(
        self,
        scored: list[tuple[RepositoryCandidate, ScoreBreakdown]],
        category: CategoryKey,
        period: DateRange,
    ) -> list[RankedRepository]:
        return [
            RankedRepository(
                rank=index,
                candidate=repository,
                score=score,
                why_included=self._why_included(repository, category, period),
            )
            for index, (repository, score) in enumerate(scored, start=1)
        ]

    def _why_included(
        self,
        repository: RepositoryCandidate,
        category: CategoryKey,
        period: DateRange,
    ) -> str:
        reasons: list[str] = []
        if category is CategoryKey.TOP_NEW and _created_within_period(repository, period):
            reasons.append("created during the reporting window")
        if category is CategoryKey.TOP_AUDIO_AI and repository.classification:
            reasons.append("clear audio-AI relevance")
        if repository.stargazers_count:
            reasons.append(f"{repository.stargazers_count} stars")
        if repository.forks_count:
            reasons.append(f"{repository.forks_count} forks")
        if repository.classification and repository.classification.tag_buckets:
            reasons.append("tags: " + ", ".join(repository.classification.tag_buckets[:3]))
        if repository.pushed_at >= period.start:
            reasons.append("active code pushes during the period")
        return "; ".join(reasons[:4]) or "audio-relevant repository with notable recent traction"
