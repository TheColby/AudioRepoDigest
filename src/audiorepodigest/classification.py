from __future__ import annotations

import re
from collections import defaultdict

from audiorepodigest.models import RelevanceResult, RepositoryCandidate

FIELD_WEIGHTS = {
    "name": 4.0,
    "topics": 3.5,
    "description": 2.5,
    "readme": 1.0,
}

BUCKET_TERMS: dict[str, tuple[str, ...]] = {
    "general_audio": (
        "audio",
        "sound",
        "waveform",
        "wav",
        "pcm",
        "loudness",
        "sample rate",
    ),
    "audio_ai": (
        "audio ai",
        "music ai",
        "speech ai",
        "voice ai",
        "audio llm",
        "generative audio",
        "text-to-audio",
        "text to audio",
        "source separation",
        "speech recognition",
        "automatic speech recognition",
        "asr",
        "tts",
        "transcription",
        "voice conversion",
        "diffusion",
        "music generation",
        "audio generation",
        "speaker diarization",
    ),
    "music_software": (
        "music",
        "midi",
        "daw",
        "sequencer",
        "notation",
        "sampler",
        "tracker",
    ),
    "dsp": (
        "dsp",
        "digital signal processing",
        "fft",
        "stft",
        "spectral",
        "filter",
        "resampler",
        "convolution",
    ),
    "speech": (
        "speech",
        "voice",
        "asr",
        "tts",
        "speaker",
        "transcription",
        "diarization",
    ),
    "spatial_audio": (
        "spatial audio",
        "ambisonics",
        "binaural",
        "immersive audio",
        "room acoustics",
        "room simulation",
    ),
    "plugins": (
        "plugin",
        "vst",
        "au",
        "clap",
        "lv2",
        "juce",
    ),
    "synthesis": (
        "synth",
        "synthesis",
        "wavetable",
        "granular",
        "fm synthesis",
        "subtractive",
        "additive synthesis",
    ),
    "mir": (
        "mir",
        "music information retrieval",
        "beat tracking",
        "chord recognition",
        "audio tagging",
        "key detection",
    ),
    "beamforming": (
        "beamforming",
        "microphone array",
        "direction of arrival",
        "doa",
    ),
    "acoustics": (
        "acoustics",
        "reverberation",
        "room impulse response",
        "rir",
        "acoustic simulation",
    ),
    "developer_tooling": (
        "sdk",
        "cli",
        "toolkit",
        "benchmark",
        "dataset",
        "evaluation",
        "inference",
        "deployment",
        "realtime",
    ),
}

DEFAULT_NEGATIVE_TERMS = (
    "car audio",
    "automotive audio",
    "audiobook",
    "podcast player",
    "spotify playlist",
    "discord bot",
    "telegram bot",
    "headphone review",
    "speaker review",
)


class RepositoryClassifier:
    """Transparent keyword-based relevance classifier."""

    def __init__(
        self,
        *,
        allowlist_topics: list[str] | None = None,
        blocklist_terms: list[str] | None = None,
        min_confidence: float = 0.38,
    ) -> None:
        self.allowlist_topics = {topic.lower().strip() for topic in allowlist_topics or [] if topic}
        self.blocklist_terms = {
            term.lower().strip()
            for term in (*DEFAULT_NEGATIVE_TERMS, *(blocklist_terms or []))
            if term
        }
        self.min_confidence = min_confidence

    def classify(
        self,
        repository: RepositoryCandidate,
        readme_text: str | None = None,
    ) -> RelevanceResult:
        fields = {
            "name": repository.full_name.lower(),
            "topics": " ".join(topic.lower() for topic in repository.topics),
            "description": repository.description.lower(),
            "readme": (readme_text or repository.readme_text or "").lower(),
        }

        bucket_scores: dict[str, float] = defaultdict(float)
        matched_terms: set[str] = set()
        excluded_terms: set[str] = set()
        positive_score = 0.0

        for bucket, terms in BUCKET_TERMS.items():
            for field_name, text in fields.items():
                for term in terms:
                    if self._matches(term, text):
                        weight = FIELD_WEIGHTS[field_name]
                        bucket_scores[bucket] += weight
                        positive_score += weight
                        matched_terms.add(term)

        allowlist_matches = self.allowlist_topics.intersection(
            {topic.lower() for topic in repository.topics}
        )
        if allowlist_matches:
            boost = 2.5 * len(allowlist_matches)
            bucket_scores["general_audio"] += boost
            positive_score += boost
            matched_terms.update(allowlist_matches)

        breadth_bonus = min(
            1.6, 0.4 * len([score for score in bucket_scores.values() if score > 0])
        )
        positive_score += breadth_bonus

        negative_penalty = 0.0
        joined_text = " ".join(fields.values())
        for term in self.blocklist_terms:
            if self._matches(term, joined_text):
                negative_penalty += 4.5
                excluded_terms.add(term)

        confidence = max(0.0, min(1.0, (positive_score - negative_penalty) / 16.0))
        audio_ai_confidence = max(0.0, min(1.0, bucket_scores.get("audio_ai", 0.0) / 8.0))

        dominant_buckets = [
            bucket
            for bucket, _score in sorted(
                bucket_scores.items(), key=lambda item: item[1], reverse=True
            )
            if _score > 0
        ]

        is_relevant = confidence >= self.min_confidence or (
            positive_score > negative_penalty
            and any(
                bucket_scores.get(bucket, 0.0) >= 3.5
                for bucket in (
                    "audio_ai",
                    "general_audio",
                    "dsp",
                    "speech",
                    "plugins",
                    "synthesis",
                    "spatial_audio",
                    "mir",
                    "beamforming",
                    "acoustics",
                )
            )
        )

        rationale = (
            f"Matched {len(matched_terms)} audio-relevant terms across "
            f"{len(dominant_buckets)} buckets; penalty terms={len(excluded_terms)}."
        )

        return RelevanceResult(
            is_relevant=is_relevant,
            confidence=round(confidence, 4),
            audio_ai_confidence=round(audio_ai_confidence, 4),
            matched_terms=sorted(matched_terms),
            excluded_terms=sorted(excluded_terms),
            tag_buckets=dominant_buckets[:5],
            bucket_scores={
                key: round(value, 2) for key, value in bucket_scores.items() if value > 0
            },
            rationale=rationale,
        )

    def _matches(self, term: str, text: str) -> bool:
        if " " in term or "-" in term:
            return term in text
        pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
