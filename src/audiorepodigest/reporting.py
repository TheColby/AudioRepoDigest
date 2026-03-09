from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from audiorepodigest import __version__
from audiorepodigest.config import DigestSettings
from audiorepodigest.models import (
    CategoryKey,
    DateRange,
    DigestReport,
    DigestSection,
    DiscoveryResult,
    ForecastSection,
    RenderBundle,
    ToCEntry,
    TrendAnalysis,
)
from audiorepodigest.utils.dates import format_timestamp

SECTION_TITLES = {
    CategoryKey.TOP_AUDIO: "🎵 Top Audio Repos",
    CategoryKey.TOP_NEW: "🆕 Top New Audio/Music Repos",
    CategoryKey.TOP_AUDIO_AI: "🤖 Top Audio AI Repos",
    CategoryKey.HONORABLE_MENTIONS: "⭐ Honorable Mentions",
}


class ReportComposer:
    """Builds a structured report model from pipeline outputs."""

    def compose(
        self,
        *,
        settings: DigestSettings,
        period: DateRange,
        period_label: str,
        discovery: DiscoveryResult,
        sections: list[DigestSection],
        trend_analysis: TrendAnalysis | None,
        forecast_section: ForecastSection | None,
    ) -> DigestReport:
        generated_at = datetime.now().astimezone()
        scanned_count = discovery.relevant_candidate_count
        selected_repo_count = sum(len(section.entries) for section in sections)
        executive_summary = self._build_executive_summary(
            sections=sections,
            trend_analysis=trend_analysis,
            scanned_count=scanned_count,
            selected_repo_count=selected_repo_count,
            frequency=settings.report_frequency.value,
        )
        toc = self._build_toc(sections, trend_analysis, forecast_section)
        methodology = [
            (
                "AudioRepoDigest scans GitHub using multiple targeted search families for "
                "audio, music, DSP, speech, plugins, MIR, synthesis, and audio-AI activity."
            ),
            (
                "Repositories are classified with transparent keyword heuristics over "
                "names, descriptions, topics, and optionally README text for borderline "
                "cases."
            ),
            (
                "Scores combine relevance confidence, popularity, activity recency, and "
                "novelty; trend and forecast sections are heuristic, deterministic, and "
                "directional rather than guarantees."
            ),
        ]

        return DigestReport(
            title="Colby's AudioRepoDigest",
            subtitle=(
                "Automated intelligence reporting for the audio, music, DSP, speech, and "
                "audio-AI GitHub ecosystem."
            ),
            generated_at=generated_at,
            period=period,
            recipient_name=settings.report_recipient_name,
            executive_summary=executive_summary,
            scanned_candidate_count=scanned_count,
            selected_repo_count=selected_repo_count,
            toc=toc,
            sections=sections,
            trend_analysis=trend_analysis,
            forecast_section=forecast_section,
            methodology=methodology,
            version=__version__,
            metadata={
                "period_label": period_label,
                "raw_candidate_count": discovery.raw_candidate_count,
                "query_count": discovery.query_count,
            },
        )

    def _build_executive_summary(
        self,
        *,
        sections: list[DigestSection],
        trend_analysis: TrendAnalysis | None,
        scanned_count: int,
        selected_repo_count: int,
        frequency: str,
    ) -> str:
        lead_repos: list[str] = []
        for section in sections[:3]:
            if section.entries:
                lead_repos.append(section.entries[0].candidate.full_name)
        standout_text = ", ".join(lead_repos[:3]) if lead_repos else "no standouts"
        dominant_text = (
            ", ".join(
                tag.replace("_", " ")
                for tag in (trend_analysis.dominant_tags[:3] if trend_analysis else [])
            )
            or "mixed audio tooling"
        )
        return (
            f"This {frequency} digest scanned {scanned_count} relevant GitHub candidates "
            f"and selected {selected_repo_count} repositories worth immediate review. "
            f"The most important names this cycle were {standout_text}, while the "
            f"dominant themes concentrated around {dominant_text}. Start with the "
            f"ranked sections, then use the trend and forecast analysis at the end to "
            f"understand where "
            f"open-source energy appears to be concentrating next."
        )

    def _build_toc(
        self,
        sections: list[DigestSection],
        trend_analysis: TrendAnalysis | None,
        forecast_section: ForecastSection | None,
    ) -> list[ToCEntry]:
        toc: list[ToCEntry] = []
        for section in sections:
            toc.append(ToCEntry(title=section.title, anchor=section.anchor))
        if trend_analysis:
            toc.append(ToCEntry(title="📈 Trend Analysis", anchor="trend-analysis"))
        if forecast_section:
            toc.append(ToCEntry(title="🔮 Where Things Are Headed", anchor="forecasts"))
        return toc


class ReportRenderer:
    """Renders HTML and plaintext email bodies, plus markdown and JSON exports."""

    def __init__(self) -> None:
        self.environment = Environment(
            loader=PackageLoader("audiorepodigest", "templates"),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, report: DigestReport, settings: DigestSettings) -> RenderBundle:
        generated_at_label = format_timestamp(report.generated_at, settings.report_timezone)
        period_label = str(report.metadata["period_label"])
        view_model = {
            "report": report,
            "generated_at_label": generated_at_label,
            "period_label": period_label,
            "timezone": settings.report_timezone,
            "verbosity": settings.report_verbosity.value,
        }
        html = self.environment.get_template("digest_email.html.j2").render(**view_model)
        text = self.environment.get_template("digest_email.txt.j2").render(**view_model)
        markdown = self._render_markdown(
            report,
            generated_at_label,
            period_label,
            settings.report_verbosity.value,
        )
        json_payload = report.model_dump(mode="json")
        subject = f"{settings.email_subject_prefix} Colby's AudioRepoDigest | {period_label}"
        return RenderBundle(
            subject=subject.strip(),
            html=html,
            text=text,
            markdown=markdown,
            json_payload=json_payload,
        )

    def write_outputs(
        self,
        bundle: RenderBundle,
        *,
        html_path: Path | None,
        markdown_path: Path | None,
        json_path: Path | None,
    ) -> list[Path]:
        written: list[Path] = []
        if html_path:
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(bundle.html, encoding="utf-8")
            written.append(html_path)
        if markdown_path and bundle.markdown:
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            markdown_path.write_text(bundle.markdown, encoding="utf-8")
            written.append(markdown_path)
        if json_path:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(bundle.json_payload, indent=2), encoding="utf-8")
            written.append(json_path)
        return written

    def _render_markdown(
        self,
        report: DigestReport,
        generated_at_label: str,
        period_label: str,
        verbosity: str,
    ) -> str:
        lines = [
            f"# {report.title}",
            "",
            report.subtitle,
            "",
            (
                f"**Report period:** {period_label} | **Generated:** {generated_at_label} | "
                f"**Recipient:** {report.recipient_name} | **Scanned:** "
                f"{report.metadata['raw_candidate_count']} raw, "
                f"{report.scanned_candidate_count} relevant, "
                f"{report.selected_repo_count} selected"
            ),
            "",
            "## 🧭 Table of Contents",
        ]
        for entry in report.toc:
            lines.append(f"- {entry.title}")

        for section in report.sections:
            lines.extend(["", f"## {section.title}", "", section.description])
            for ranked in section.entries:
                repository = ranked.candidate
                score_details = ", ".join(
                    f"{key}={value:.1f}" for key, value in ranked.score.components.items()
                )
                lines.extend(
                    [
                        "",
                        f"### {ranked.rank}. [{repository.full_name}]({repository.html_url})",
                        f"- Description: {repository.description or 'No description provided.'}",
                        f"- Tags: {', '.join(repository.primary_tags) or 'n/a'}",
                    ]
                )
                if verbosity == "detailed":
                    lines.extend(
                        [
                            (
                                f"- Metadata: owner={repository.owner}, "
                                f"language={repository.language or 'n/a'}, "
                                f"created={repository.created_at.date().isoformat()}, "
                                f"updated={repository.updated_at.date().isoformat()}"
                            ),
                            (
                                f"- Stats: {repository.stargazers_count} stars, "
                                f"{repository.forks_count} forks, "
                                f"{repository.open_issues_count} open issues, "
                                f"{repository.watchers_count} watchers"
                            ),
                            f"- Score: {ranked.score.total_score:.2f} | {score_details}",
                            f"- Why it made the list: {ranked.why_included}",
                        ]
                    )
                else:
                    lines.append(
                        "- Details: stats/score/rationale are available in HTML expandable "
                        "sections."
                    )

        if report.trend_analysis:
            lines.extend(["", "## 📈 Trend Analysis", "", report.trend_analysis.headline])
            for paragraph in report.trend_analysis.narrative_sections:
                lines.extend(["", paragraph])

        if report.forecast_section:
            lines.extend(["", "## 🔮 Where Things Are Headed", "", report.forecast_section.intro])
            for item in report.forecast_section.items:
                lines.extend(
                    [
                        "",
                        f"### {item.title}",
                        item.estimate,
                        "",
                        f"Signals: {item.signals}",
                        "",
                        f"Implications: {item.implications}",
                    ]
                )

        lines.extend(["", "## 🧪 Methodology"])
        lines.extend([f"- {item}" for item in report.methodology])
        lines.extend(["", f"_Generated by AudioRepoDigest v{report.version}_"])
        lines.extend(
            [
                "",
                (
                    "Want to generate your own customized automated, scheduled report like "
                    "this? Check out my repo at "
                    "https://github.com/TheColby/AudioRepoDigest"
                ),
            ]
        )
        return "\n".join(lines)


def build_section(
    category: CategoryKey,
    entries: list[Any],
) -> DigestSection:
    anchor = category.value.replace("_", "-")
    descriptions = {
        CategoryKey.TOP_AUDIO: (
            "Established repositories showing the strongest mix of relevance, "
            "traction, and recent activity."
        ),
        CategoryKey.TOP_NEW: (
            "Repositories created during the reporting window that already show credible momentum."
        ),
        CategoryKey.TOP_AUDIO_AI: (
            "Repositories centered on speech, generative audio, music AI, voice "
            "tooling, or adjacent audio-ML infrastructure."
        ),
        CategoryKey.HONORABLE_MENTIONS: (
            "Additional repositories worth scanning even if they did not make the "
            "core ranked sections."
        ),
    }
    return DigestSection(
        category=category,
        title=SECTION_TITLES[category],
        anchor=anchor,
        description=descriptions[category],
        entries=entries,
    )
