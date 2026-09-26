from __future__ import annotations

from audiorepodigest.models import TrendAnalysis
from audiorepodigest.repo_ideas import RepoIdeaEngine


def test_repo_idea_engine_generates_ten_distinct_ideas() -> None:
    analysis = TrendAnalysis(
        headline="Audio AI and DSP activity increased.",
        dominant_tags=["audio_ai", "speech", "dsp", "plugins", "synthesis"],
    )

    ideas = RepoIdeaEngine().generate(analysis, [])

    assert len(ideas.ideas) == 10
    assert len({idea.title for idea in ideas.ideas}) == 10
    assert ideas.ideas[0].source_tags == ["audio_ai"]
    assert "First release" not in ideas.ideas[0].premise
