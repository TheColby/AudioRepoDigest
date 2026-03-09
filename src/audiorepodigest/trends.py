from __future__ import annotations

from collections import Counter

from audiorepodigest.models import DigestSection, RepositoryCandidate, TrendAnalysis

STOPWORDS = {
    "audio",
    "music",
    "repo",
    "repository",
    "tool",
    "tools",
    "framework",
    "library",
    "python",
    "rust",
    "project",
    "open",
    "source",
    "for",
    "with",
    "and",
    "the",
    "using",
}

SEGMENT_MAP = {
    "audio_ai": "music generation / audio AI",
    "speech": "speech / voice AI",
    "plugins": "plugin ecosystems",
    "spatial_audio": "spatial audio",
    "beamforming": "spatial audio",
    "acoustics": "spatial audio",
    "developer_tooling": "developer tooling",
    "dsp": "tooling",
    "synthesis": "creative tools",
    "music_software": "creative tools",
    "mir": "research",
}


class TrendAnalyzer:
    """Heuristic and deterministic trend-analysis engine."""

    def analyze(
        self,
        sections: list[DigestSection],
        candidate_pool: list[RepositoryCandidate],
    ) -> TrendAnalysis:
        selected_repositories = [
            entry.candidate for section in sections for entry in section.entries
        ]
        if not selected_repositories:
            return TrendAnalysis(
                headline="No trend analysis was produced because no repositories were selected.",
                methodology_note="Trend analysis requires at least one selected repository.",
            )

        theme_counts = Counter()
        candidate_theme_counts = Counter()
        segment_counts = Counter()
        keyword_counts = Counter()

        for repository in candidate_pool:
            if repository.classification:
                candidate_theme_counts.update(repository.classification.tag_buckets)

        for repository in selected_repositories:
            classification = repository.classification
            if classification:
                theme_counts.update(classification.tag_buckets)
            segment_counts.update(self._infer_segments(repository))
            keyword_counts.update(self._extract_keywords(repository))

        dominant_tags = [tag for tag, _count in theme_counts.most_common(6)]
        repeated_keywords = [
            keyword for keyword, count in keyword_counts.most_common(10) if count >= 2
        ]
        underrepresented = self._underrepresented(theme_counts, candidate_theme_counts)
        headline = self._build_headline(theme_counts, segment_counts)
        narrative_sections = self._build_narrative(
            theme_counts=theme_counts,
            segment_counts=segment_counts,
            underrepresented=underrepresented,
        )

        return TrendAnalysis(
            headline=headline,
            dominant_tags=dominant_tags,
            theme_counts=dict(theme_counts.most_common()),
            segment_counts=dict(segment_counts.most_common()),
            repeated_keywords=repeated_keywords,
            underrepresented_segments=underrepresented,
            narrative_sections=narrative_sections,
            methodology_note=(
                "Trend analysis aggregates selected repositories plus the wider "
                "candidate pool, then "
                "compares tag and segment frequency to highlight concentration and gaps."
            ),
        )

    def _infer_segments(self, repository: RepositoryCandidate) -> list[str]:
        segments: set[str] = set()
        if repository.classification:
            for bucket in repository.classification.tag_buckets:
                segment = SEGMENT_MAP.get(bucket)
                if segment:
                    segments.add(segment)

        description = repository.description.lower()
        if any(
            term in description for term in ("benchmark", "dataset", "research", "paper", "model")
        ):
            segments.add("research")
        if any(term in description for term in ("sdk", "api", "realtime", "production", "deploy")):
            segments.add("productization")
        if "infra" in description or "pipeline" in description:
            segments.add("open-source infrastructure")
        return list(segments)

    def _extract_keywords(self, repository: RepositoryCandidate) -> list[str]:
        raw_tokens = (
            " ".join([repository.name, repository.description, *repository.topics])
            .replace("/", " ")
            .replace("-", " ")
        )
        keywords: list[str] = []
        for token in raw_tokens.lower().split():
            cleaned = "".join(character for character in token if character.isalnum())
            if len(cleaned) < 4 or cleaned in STOPWORDS:
                continue
            keywords.append(cleaned)
        return keywords

    def _underrepresented(
        self,
        selected_counts: Counter[str],
        candidate_counts: Counter[str],
    ) -> list[str]:
        underrepresented: list[str] = []
        for bucket, candidate_count in candidate_counts.items():
            if candidate_count < 3:
                continue
            selected_count = selected_counts.get(bucket, 0)
            if selected_count == 0 or selected_count < candidate_count / 3:
                underrepresented.append(bucket)
        return underrepresented[:5]

    def _build_headline(self, theme_counts: Counter[str], segment_counts: Counter[str]) -> str:
        dominant_theme = theme_counts.most_common(1)[0][0] if theme_counts else "general_audio"
        dominant_segment = segment_counts.most_common(1)[0][0] if segment_counts else "tooling"
        return (
            f"The period leaned most heavily toward {dominant_theme.replace('_', ' ')} work, with "
            f"{dominant_segment} drawing the clearest concentration of attention."
        )

    def _build_narrative(
        self,
        *,
        theme_counts: Counter[str],
        segment_counts: Counter[str],
        underrepresented: list[str],
    ) -> list[str]:
        top_themes = ", ".join(tag.replace("_", " ") for tag, _count in theme_counts.most_common(4))
        top_segments = ", ".join(segment for segment, _count in segment_counts.most_common(4))

        audio_ai_strength = theme_counts.get("audio_ai", 0) + theme_counts.get("speech", 0)
        traditional_strength = (
            theme_counts.get("dsp", 0)
            + theme_counts.get("plugins", 0)
            + theme_counts.get("synthesis", 0)
        )
        if audio_ai_strength > traditional_strength * 1.2:
            balance_statement = (
                "Developer attention leaned more toward audio-AI and speech-centric work than "
                "traditional DSP or plugin infrastructure."
            )
        elif traditional_strength > audio_ai_strength * 1.2:
            balance_statement = (
                "Traditional DSP, plugins, and synthesis infrastructure held up better than the "
                "current audio-AI wave in this selection."
            )
        else:
            balance_statement = (
                "Audio-AI and classic audio-engineering work were relatively balanced, suggesting "
                "a mixed market rather than a single dominant narrative."
            )

        if "productization" in segment_counts and segment_counts["productization"] >= 2:
            commercialization = (
                "There were visible signs of productization, with repos emphasizing deployability, "
                "SDK layers, or real-time serving rather than just experiments."
            )
        else:
            commercialization = (
                "The selected repos still skewed more toward experimentation, tooling, and "
                "open-source building blocks than polished product surfaces."
            )

        absences = (
            "Notable gaps this period included "
            + ", ".join(bucket.replace("_", " ") for bucket in underrepresented)
            + "."
            if underrepresented
            else "No single expected audio segment was meaningfully absent from the candidate pool."
        )

        return [
            (
                f"Dominant technical themes were {top_themes}. "
                f"The most visible activity clusters were {top_segments}."
            ),
            f"{balance_statement} {commercialization}",
            absences,
        ]
