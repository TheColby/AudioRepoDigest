from __future__ import annotations

from audiorepodigest.classification import RepositoryClassifier

from .conftest import make_repository


def test_classifier_identifies_audio_ai_repository() -> None:
    repository = make_repository(
        full_name="acme/neural-audio-diffusion",
        description="Text-to-audio diffusion, speech synthesis, and voice AI toolkit.",
        topics=["audio", "speech", "machine-learning", "generative-audio"],
    )

    result = RepositoryClassifier().classify(repository)
    assert result.is_relevant
    assert "audio_ai" in result.tag_buckets
    assert result.audio_ai_confidence > 0.4


def test_classifier_filters_false_positive() -> None:
    repository = make_repository(
        full_name="acme/car-audio-guide",
        description="Car audio speaker review and podcast player directory.",
        topics=["cars", "reviews"],
    )

    result = RepositoryClassifier().classify(repository)
    assert not result.is_relevant
    assert "car audio" in result.excluded_terms
