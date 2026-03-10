from __future__ import annotations

from audiorepodigest.models import CategoryKey
from audiorepodigest.reporting import build_section


def test_build_section_uses_expected_anchor() -> None:
    section = build_section(CategoryKey.TOP_AUDIO_AI, [])
    assert section.anchor == "top-audio-ai"
    assert section.title == "🤖 Top Audio AI Repos"


def test_renderer_outputs_html_text_and_markdown(rendered_report_bundle) -> None:
    report, bundle = rendered_report_bundle
    assert "Table of Contents" in bundle.html
    assert "EXECUTIVE SUMMARY" not in bundle.text
    assert report.sections[0].entries[0].candidate.html_url in bundle.html
    assert report.sections[0].entries[0].candidate.html_url in bundle.text
    assert "Stats:" not in bundle.html
    assert "Where Things Are Headed" in bundle.markdown
