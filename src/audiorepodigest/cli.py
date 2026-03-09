from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from audiorepodigest.config import DigestSettings, load_settings
from audiorepodigest.emailer import EmailSender
from audiorepodigest.logging import configure_logging
from audiorepodigest.models import CategoryKey
from audiorepodigest.pipeline import AudioRepoDigestPipeline
from audiorepodigest.utils.dates import parse_date, resolve_period

app = typer.Typer(help="AudioRepoDigest CLI")
console = Console()


def _load_runtime(config: Path | None) -> DigestSettings:
    settings = load_settings(config)
    configure_logging(settings.log_level)
    return settings


def _resolve_period(
    settings: DigestSettings,
    start_date: str | None,
    end_date: str | None,
):
    parsed_start = parse_date(start_date)
    parsed_end = parse_date(end_date)
    return resolve_period(
        frequency=settings.report_frequency,
        timezone=settings.report_timezone,
        start_date=parsed_start,
        end_date=parsed_end,
        lookback_days=settings.report_lookback_days,
    )


def _parse_categories(values: list[str] | None) -> list[CategoryKey] | None:
    if not values:
        return None
    categories: list[CategoryKey] = []
    for value in values:
        categories.append(CategoryKey(value))
    return categories


def _write_outputs(
    pipeline: AudioRepoDigestPipeline,
    *,
    html_path: Path | None,
    markdown_path: Path | None,
    json_path: Path | None,
    bundle,
) -> None:
    written = pipeline.report_renderer.write_outputs(
        bundle,
        html_path=html_path,
        markdown_path=markdown_path,
        json_path=json_path,
    )
    for path in written:
        console.print(f"Wrote [bold]{path}[/bold]")


@app.command()
def run(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    start_date: Annotated[
        str | None, typer.Option(help="Explicit period start date (YYYY-MM-DD).")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option(help="Explicit period end date (YYYY-MM-DD).")
    ] = None,
    category: Annotated[
        list[str] | None, typer.Option("--category", help="Category key to include.")
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Render but do not send email.")] = False,
    recipient_email: Annotated[str | None, typer.Option(help="Override recipient email.")] = None,
    recipient_name: Annotated[str | None, typer.Option(help="Override recipient name.")] = None,
) -> None:
    settings = _load_runtime(config)
    period = _resolve_period(settings, start_date, end_date)
    with AudioRepoDigestPipeline(settings) as pipeline:
        result = pipeline.build_digest(period=period, categories=_parse_categories(category))
        _write_outputs(
            pipeline,
            html_path=settings.output_html_path,
            markdown_path=settings.output_markdown_path,
            json_path=settings.output_json_path,
            bundle=result.render_bundle,
        )
        if dry_run:
            console.print(result.render_bundle.text)
            return
        EmailSender(settings).send_render_bundle(
            result.report,
            result.render_bundle,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
        )


@app.command()
def preview(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    start_date: Annotated[
        str | None, typer.Option(help="Explicit period start date (YYYY-MM-DD).")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option(help="Explicit period end date (YYYY-MM-DD).")
    ] = None,
    category: Annotated[
        list[str] | None, typer.Option("--category", help="Category key to include.")
    ] = None,
    output_html: Annotated[Path | None, typer.Option(help="Override HTML preview path.")] = None,
    output_markdown: Annotated[
        Path | None, typer.Option(help="Override markdown preview path.")
    ] = None,
    output_json: Annotated[Path | None, typer.Option(help="Override JSON preview path.")] = None,
    print_text: Annotated[
        bool, typer.Option(help="Print plaintext report to the terminal.")
    ] = True,
) -> None:
    settings = _load_runtime(config)
    period = _resolve_period(settings, start_date, end_date)
    with AudioRepoDigestPipeline(settings) as pipeline:
        result = pipeline.build_digest(period=period, categories=_parse_categories(category))
        _write_outputs(
            pipeline,
            html_path=output_html or settings.output_html_path,
            markdown_path=output_markdown or settings.output_markdown_path,
            json_path=output_json or settings.output_json_path,
            bundle=result.render_bundle,
        )
        if print_text:
            console.print(result.render_bundle.text)


@app.command("send-test-email")
def send_test_email(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    recipient_email: Annotated[
        str | None, typer.Option(help="Override recipient email for testing.")
    ] = None,
    recipient_name: Annotated[
        str | None, typer.Option(help="Override recipient name for testing.")
    ] = None,
) -> None:
    settings = _load_runtime(config)
    with AudioRepoDigestPipeline(settings) as pipeline:
        result = pipeline.build_digest()
        EmailSender(settings).send_render_bundle(
            result.report,
            result.render_bundle,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
        )


@app.command("validate-config")
def validate_config(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
) -> None:
    settings = _load_runtime(config)
    table = Table(title="Resolved AudioRepoDigest Configuration")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row(
        "Recipient", f"{settings.report_recipient_name} <{settings.report_recipient_email}>"
    )
    table.add_row("Frequency", settings.report_frequency.value)
    table.add_row("Effective cron", settings.effective_cron)
    table.add_row("Timezone", settings.report_timezone)
    table.add_row(
        "Top N main/new/audio-ai",
        f"{settings.top_n_main}/{settings.top_n_new}/{settings.top_n_audio_ai}",
    )
    table.add_row("HTML output", str(settings.output_html_path))
    table.add_row("Markdown output", str(settings.output_markdown_path))
    table.add_row("JSON output", str(settings.output_json_path))
    console.print(table)


@app.command("list-candidates")
def list_candidates(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    start_date: Annotated[
        str | None, typer.Option(help="Explicit period start date (YYYY-MM-DD).")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option(help="Explicit period end date (YYYY-MM-DD).")
    ] = None,
    limit: Annotated[int, typer.Option(help="Maximum rows to show.")] = 25,
) -> None:
    settings = _load_runtime(config)
    period = _resolve_period(settings, start_date, end_date)
    with AudioRepoDigestPipeline(settings) as pipeline:
        candidates = pipeline.collect_candidates(period=period)[:limit]
    table = Table(title=f"Candidates for {period.label}")
    table.add_column("Repository")
    table.add_column("Confidence")
    table.add_column("Stars")
    table.add_column("Tags")
    table.add_column("Updated")
    for candidate in candidates:
        table.add_row(
            candidate.full_name,
            f"{candidate.classification.confidence:.2f}" if candidate.classification else "n/a",
            str(candidate.stargazers_count),
            ", ".join(candidate.primary_tags) or "n/a",
            candidate.updated_at.date().isoformat(),
        )
    console.print(table)


@app.command("explain-score")
def explain_score(
    repository: Annotated[str, typer.Argument(help="Repository full name, e.g. owner/name.")],
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    start_date: Annotated[
        str | None, typer.Option(help="Explicit period start date (YYYY-MM-DD).")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option(help="Explicit period end date (YYYY-MM-DD).")
    ] = None,
) -> None:
    settings = _load_runtime(config)
    period = _resolve_period(settings, start_date, end_date)
    with AudioRepoDigestPipeline(settings) as pipeline:
        explanations = pipeline.explain_repository(repository, period=period)
    table = Table(title=f"Score explanation for {repository}")
    table.add_column("Category")
    table.add_column("Total")
    table.add_column("Components")
    for category_key, breakdown in explanations.items():
        component_text = ", ".join(
            f"{key}={value:.1f}" for key, value in breakdown.components.items()
        )
        table.add_row(category_key.value, f"{breakdown.total_score:.2f}", component_text)
    console.print(table)


@app.command()
def trends(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    start_date: Annotated[
        str | None, typer.Option(help="Explicit period start date (YYYY-MM-DD).")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option(help="Explicit period end date (YYYY-MM-DD).")
    ] = None,
) -> None:
    settings = _load_runtime(config)
    period = _resolve_period(settings, start_date, end_date)
    with AudioRepoDigestPipeline(settings) as pipeline:
        result = pipeline.build_digest(period=period)
    if result.report.trend_analysis is None:
        console.print("Trend analysis is disabled.")
        raise typer.Exit(code=0)
    console.print(f"[bold]{result.report.trend_analysis.headline}[/bold]")
    for paragraph in result.report.trend_analysis.narrative_sections:
        console.print(paragraph)
    if result.report.forecast_section:
        console.print("")
        console.print(f"[bold]{result.report.forecast_section.headline}[/bold]")
        console.print(result.report.forecast_section.intro)
        for item in result.report.forecast_section.items:
            console.print(f"- {item.title}: {item.estimate}")


@app.command()
def export(
    config: Annotated[Path | None, typer.Option(help="Optional YAML config path.")] = None,
    start_date: Annotated[
        str | None, typer.Option(help="Explicit period start date (YYYY-MM-DD).")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option(help="Explicit period end date (YYYY-MM-DD).")
    ] = None,
    output_html: Annotated[Path | None, typer.Option(help="HTML export path.")] = None,
    output_markdown: Annotated[Path | None, typer.Option(help="Markdown export path.")] = None,
    output_json: Annotated[Path | None, typer.Option(help="JSON export path.")] = None,
) -> None:
    settings = _load_runtime(config)
    period = _resolve_period(settings, start_date, end_date)
    with AudioRepoDigestPipeline(settings) as pipeline:
        result = pipeline.build_digest(period=period)
        _write_outputs(
            pipeline,
            html_path=output_html or settings.output_html_path,
            markdown_path=output_markdown or settings.output_markdown_path,
            json_path=output_json or settings.output_json_path,
            bundle=result.render_bundle,
        )


if __name__ == "__main__":
    app()
