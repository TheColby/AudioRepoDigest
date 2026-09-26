from __future__ import annotations

from audiorepodigest.models import DigestSection, RepoIdea, RepoIdeaSection, TrendAnalysis

IDEA_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "audio_ai": (
        "Audio Model Evaluation Harness",
        "A reproducible benchmark runner for comparing generative-audio models on prompt "
        "adherence, latency, cost, and artifact detection.",
        "Ship a CLI that runs a small fixed prompt suite against two providers and writes "
        "a shareable HTML scorecard.",
    ),
    "speech": (
        "Voice Workflow Quality Gate",
        "A local-first checker that scores speech recordings and TTS output for clipping, "
        "silence, intelligibility proxies, loudness, and timing drift.",
        "Ship a CLI that accepts WAV files and emits JSON plus a compact HTML report.",
    ),
    "dsp": (
        "DSP Recipe Compiler",
        "A declarative format for describing practical audio-processing chains and compiling "
        "them into Python, JUCE, or Web Audio implementations.",
        "Ship five canonical recipes and a renderer that produces a runnable Python pipeline.",
    ),
    "plugins": (
        "Plugin Compatibility Snapshot",
        "A community-maintained scanner that records plugin format, platform support, "
        "architecture, and host compatibility in a machine-readable catalog.",
        "Ship a CLI scanner for VST3 and CLAP metadata with a static JSON catalog.",
    ),
    "synthesis": (
        "Synthesis Patch Diff",
        "A semantic diff tool for synth patches that explains which audible controls changed "
        "rather than showing raw preset-file differences.",
        "Ship support for one open preset format and a text plus HTML change report.",
    ),
    "spatial_audio": (
        "Spatial Mix Regression Suite",
        "A test harness that renders reference multichannel scenes and detects channel-order, "
        "headroom, and localization regressions.",
        "Ship ambisonic decode fixtures, basic energy checks, and CI-friendly pass/fail output.",
    ),
    "beamforming": (
        "Microphone Array Sandbox",
        "An interactive library for simulating array geometry, steering directions, and beam "
        "patterns from simple configuration files.",
        "Ship a Python API, three common array presets, and polar-plot export.",
    ),
    "acoustics": (
        "Room Response Notebook Kit",
        "A small toolkit that turns room measurements into comparable decay, clarity, and "
        "spectral-balance reports.",
        "Ship WAV ingestion, RT60 estimates, and a self-contained report export.",
    ),
    "mir": (
        "Music Corpus Change Tracker",
        "A dataset-aware tool that fingerprints music collections and tracks changes in "
        "metadata, embeddings, and annotation coverage.",
        "Ship manifest generation, duplicate detection, and a dataset-diff command.",
    ),
    "music_software": (
        "Session Interchange Linter",
        "A validator for DAW-adjacent interchange files that catches missing media, tempo-map "
        "inconsistencies, and unsafe routing assumptions.",
        "Ship a MIDI-first validator with clear repair suggestions.",
    ),
    "developer_tooling": (
        "Audio Project Repro Kit",
        "A lightweight project manifest and command-line tool for making audio experiments "
        "reproducible across machines.",
        "Ship a lockfile, environment check, and one-command artifact bundle export.",
    ),
    "general_audio": (
        "Audio Asset Provenance Ledger",
        "A local tool that records source, edits, export settings, and checksums for audio "
        "assets without requiring a database service.",
        "Ship file watching, sidecar metadata, and a searchable CLI history.",
    ),
}

FALLBACK_TAGS = [
    "audio_ai", "speech", "dsp", "plugins", "synthesis", "spatial_audio", "mir",
    "developer_tooling", "general_audio",
]


class RepoIdeaEngine:
    """Generates practical, deterministic project ideas from weekly ecosystem signals."""

    def generate(
        self,
        trend_analysis: TrendAnalysis | None,
        sections: list[DigestSection],
        *,
        limit: int = 5,
    ) -> RepoIdeaSection:
        selected = [entry.candidate for section in sections for entry in section.entries]
        trend_tags = trend_analysis.dominant_tags if trend_analysis else []
        gap_tags = trend_analysis.underrepresented_segments if trend_analysis else []
        tags = self._ordered_unique([*trend_tags, *gap_tags, *FALLBACK_TAGS])
        chosen_tags = [tag for tag in tags if tag in IDEA_TEMPLATES][:limit]
        ideas: list[RepoIdea] = []

        for index, tag in enumerate(chosen_tags, start=1):
            title, premise, first_release = IDEA_TEMPLATES[tag]
            inspirations = [repo.full_name for repo in selected if tag in repo.primary_tags][:2]
            signal = tag.replace("_", " ").title()
            why_now = f"{signal} appeared in this week's ecosystem signals."
            if inspirations:
                why_now = f"{why_now[:-1]} with examples including {', '.join(inspirations)}."
            ideas.append(
                RepoIdea(
                    title=f"{index}. {title}",
                    premise=premise,
                    why_now=why_now,
                    first_release=first_release,
                    source_tags=[tag],
                    inspiration_repositories=inspirations,
                )
            )

        return RepoIdeaSection(
            headline="5 Repo Ideas to Build This Week",
            intro=(
                "These are deterministic build prompts derived from this week's repository "
                "signals. They are starting points, not investment advice or certainty."
            ),
            ideas=ideas,
        )

    @staticmethod
    def _ordered_unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
