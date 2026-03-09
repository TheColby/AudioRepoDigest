from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class ReportFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class CategoryKey(StrEnum):
    TOP_AUDIO = "top_audio"
    TOP_NEW = "top_new"
    TOP_AUDIO_AI = "top_audio_ai"
    HONORABLE_MENTIONS = "honorable_mentions"


class DateRange(BaseModel):
    start: datetime
    end: datetime
    label: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days(self) -> int:
        return max(1, math.ceil((self.end - self.start).total_seconds() / 86_400))


class RelevanceResult(BaseModel):
    is_relevant: bool
    confidence: float
    audio_ai_confidence: float = 0.0
    matched_terms: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    tag_buckets: list[str] = Field(default_factory=list)
    bucket_scores: dict[str, float] = Field(default_factory=dict)
    rationale: str = ""


class RepositoryCandidate(BaseModel):
    id: int
    full_name: str
    name: str
    owner: str
    html_url: str
    description: str = ""
    topics: list[str] = Field(default_factory=list)
    language: str | None = None
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    stargazers_count: int = 0
    forks_count: int = 0
    watchers_count: int = 0
    open_issues_count: int = 0
    archived: bool = False
    fork: bool = False
    readme_text: str | None = None
    source_queries: list[str] = Field(default_factory=list)
    classification: RelevanceResult | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict, repr=False)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def primary_tags(self) -> list[str]:
        if self.classification and self.classification.tag_buckets:
            return self.classification.tag_buckets[:4]
        return self.topics[:4]


class ScoreBreakdown(BaseModel):
    category: CategoryKey
    total_score: float
    components: dict[str, float]
    explanation: str


class RankedRepository(BaseModel):
    rank: int
    candidate: RepositoryCandidate
    score: ScoreBreakdown
    why_included: str


class DigestSection(BaseModel):
    category: CategoryKey
    title: str
    anchor: str
    description: str
    entries: list[RankedRepository] = Field(default_factory=list)


class TrendAnalysis(BaseModel):
    headline: str
    dominant_tags: list[str] = Field(default_factory=list)
    theme_counts: dict[str, int] = Field(default_factory=dict)
    segment_counts: dict[str, int] = Field(default_factory=dict)
    repeated_keywords: list[str] = Field(default_factory=list)
    underrepresented_segments: list[str] = Field(default_factory=list)
    narrative_sections: list[str] = Field(default_factory=list)
    methodology_note: str = ""


class ForecastItem(BaseModel):
    title: str
    estimate: str
    signals: str
    implications: str


class ForecastSection(BaseModel):
    headline: str
    intro: str
    items: list[ForecastItem] = Field(default_factory=list)


class ToCEntry(BaseModel):
    title: str
    anchor: str


class DigestReport(BaseModel):
    title: str
    subtitle: str
    generated_at: datetime
    period: DateRange
    recipient_name: str
    executive_summary: str
    scanned_candidate_count: int
    selected_repo_count: int
    toc: list[ToCEntry] = Field(default_factory=list)
    sections: list[DigestSection] = Field(default_factory=list)
    trend_analysis: TrendAnalysis | None = None
    forecast_section: ForecastSection | None = None
    methodology: list[str] = Field(default_factory=list)
    version: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderBundle(BaseModel):
    subject: str
    html: str
    text: str
    markdown: str | None = None
    json_payload: dict[str, Any] = Field(default_factory=dict)


class DiscoveryResult(BaseModel):
    candidates: list[RepositoryCandidate] = Field(default_factory=list)
    query_count: int = 0
    raw_candidate_count: int = 0
    relevant_candidate_count: int = 0


class PipelineResult(BaseModel):
    report: DigestReport
    render_bundle: RenderBundle
    discovery: DiscoveryResult
