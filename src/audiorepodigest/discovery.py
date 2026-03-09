from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from audiorepodigest.classification import RepositoryClassifier
from audiorepodigest.config import DigestSettings
from audiorepodigest.github_client import GitHubClient
from audiorepodigest.logging import get_logger
from audiorepodigest.models import DateRange, DiscoveryResult, RepositoryCandidate

logger = get_logger(__name__)


@dataclass(frozen=True)
class QueryDefinition:
    name: str
    query: str
    sort: str = "updated"


class RepositoryDiscoverer:
    """Discovers repositories through multiple targeted GitHub search families."""

    def __init__(
        self,
        client: GitHubClient,
        classifier: RepositoryClassifier,
        settings: DigestSettings,
    ) -> None:
        self.client = client
        self.classifier = classifier
        self.settings = settings

    def discover(self, period: DateRange) -> DiscoveryResult:
        queries = self._build_queries(period)
        per_query_limit = max(12, self.settings.max_candidates_to_scan // max(1, len(queries)))

        raw_candidate_count = 0
        deduplicated: dict[str, RepositoryCandidate] = {}

        for query in queries:
            repositories = self.client.search_repositories(
                query.query,
                sort=query.sort,
                limit=per_query_limit,
            )
            raw_candidate_count += len(repositories)
            for repository in repositories:
                existing = deduplicated.get(repository.full_name)
                if existing is None:
                    deduplicated[repository.full_name] = repository
                else:
                    for source_query in repository.source_queries:
                        if source_query not in existing.source_queries:
                            existing.source_queries.append(source_query)

        candidates = list(deduplicated.values())
        for repository in candidates:
            repository.classification = self.classifier.classify(repository)

        borderline = [
            repository
            for repository in candidates
            if repository.classification
            and not repository.classification.is_relevant
            and repository.classification.confidence
            >= max(self.classifier.min_confidence - 0.12, 0)
        ][: self.settings.readme_fallback_limit]

        for repository in borderline:
            try:
                repository.readme_text = self.client.get_readme_text(repository.full_name)
            except Exception as exc:  # pragma: no cover - defensive runtime handling
                logger.warning("Failed to fetch README for %s: %s", repository.full_name, exc)
                continue
            repository.classification = self.classifier.classify(
                repository,
                readme_text=repository.readme_text,
            )

        relevant_candidates = [
            repository
            for repository in candidates
            if repository.classification and repository.classification.is_relevant
        ]
        relevant_candidates.sort(
            key=lambda repository: (
                repository.classification.confidence if repository.classification else 0.0,
                repository.stargazers_count,
                repository.pushed_at.timestamp(),
            ),
            reverse=True,
        )
        trimmed_candidates = relevant_candidates[: self.settings.max_candidates_to_scan]
        logger.info(
            "Discovery completed: %s raw results, %s relevant candidates, %s queries.",
            raw_candidate_count,
            len(trimmed_candidates),
            len(queries),
        )
        return DiscoveryResult(
            candidates=trimmed_candidates,
            query_count=len(queries),
            raw_candidate_count=raw_candidate_count,
            relevant_candidate_count=len(trimmed_candidates),
        )

    def _build_queries(self, period: DateRange) -> list[QueryDefinition]:
        activity_floor = (
            period.start - timedelta(days=self.settings.github_search_window_days)
        ).date()
        created_floor = period.start.date().isoformat()
        created_ceiling = (period.end - timedelta(days=1)).date().isoformat()
        pushed_clause = f"pushed:>={activity_floor.isoformat()}"
        created_clause = f"created:{created_floor}..{created_ceiling}"

        return [
            QueryDefinition(
                "topic_audio", f"topic:audio archived:false fork:false {pushed_clause}"
            ),
            QueryDefinition(
                "topic_music", f"topic:music archived:false fork:false {pushed_clause}"
            ),
            QueryDefinition("topic_dsp", f"topic:dsp archived:false fork:false {pushed_clause}"),
            QueryDefinition(
                "topic_speech", f"topic:speech archived:false fork:false {pushed_clause}"
            ),
            QueryDefinition(
                "topic_mir",
                f"topic:music-information-retrieval archived:false fork:false {pushed_clause}",
            ),
            QueryDefinition(
                "topic_synth", f"topic:synthesizer archived:false fork:false {pushed_clause}"
            ),
            QueryDefinition(
                "audio_text", f"audio in:name,description archived:false fork:false {pushed_clause}"
            ),
            QueryDefinition(
                "music_text", f"music in:name,description archived:false fork:false {pushed_clause}"
            ),
            QueryDefinition(
                "speech_text",
                f"speech in:name,description archived:false fork:false {pushed_clause}",
            ),
            QueryDefinition(
                "audio_ai_text",
                f'"generative audio" in:name,description archived:false fork:false {pushed_clause}',
            ),
            QueryDefinition(
                "new_audio",
                f"audio in:name,description archived:false fork:false {created_clause}",
                sort="stars",
            ),
            QueryDefinition(
                "new_music",
                f"music in:name,description archived:false fork:false {created_clause}",
                sort="stars",
            ),
            QueryDefinition(
                "new_audio_ai",
                f'"audio ai" in:name,description archived:false fork:false {created_clause}',
                sort="stars",
            ),
        ]
