from __future__ import annotations

from audiorepodigest.models import DigestSection, ForecastItem, ForecastSection, TrendAnalysis


class ForecastEngine:
    """Produces explicitly heuristic and directional forecasts."""

    def generate(
        self,
        trend_analysis: TrendAnalysis,
        sections: list[DigestSection],
    ) -> ForecastSection:
        selected_repos = [entry.candidate for section in sections for entry in section.entries]
        dominant_tags = trend_analysis.dominant_tags
        dominant_tag_text = ", ".join(tag.replace("_", " ") for tag in dominant_tags[:3]) or "audio"
        repeated_keywords = ", ".join(trend_analysis.repeated_keywords[:5]) or "tooling"

        if "audio_ai" in dominant_tags or "speech" in dominant_tags:
            growth_estimate = (
                "Directional estimate: open-source energy is likely to keep concentrating around "
                "speech pipelines, deployable generative-audio stacks, and model-adjacent tooling."
            )
        elif "dsp" in dominant_tags or "plugins" in dominant_tags:
            growth_estimate = (
                "Directional estimate: the next few weeks are likely to favor pragmatic DSP, "
                "plugin ecosystem work, and reusable audio infrastructure over net-new "
                "research repos."
            )
        else:
            growth_estimate = (
                "Directional estimate: growth is likely to remain fragmented across audio "
                "tooling, music software, and AI-assisted production workflows rather than "
                "collapsing into one theme."
            )

        if "audio_ai" in dominant_tags:
            saturated_estimate = (
                "Heuristic estimate: thin wrappers around foundation models, notebook-first "
                "demos, and undifferentiated text-to-audio experiments are the most likely "
                "areas to feel saturated."
            )
        else:
            saturated_estimate = (
                "Heuristic estimate: generic utility repos without a clear workflow angle or "
                "technical "
                "edge are the most likely to struggle for attention."
            )

        breakout_estimate = (
            "Directional estimate: likely breakout archetypes are repos that bridge two "
            "adjacent layers, such as model serving plus audio UX, MIR plus creator tooling, "
            "or DSP kernels packaged as "
            "production-ready developer infrastructure."
        )

        implication_estimate = (
            "Heuristic estimate: practitioners and founders should watch maintainers building "
            "repeatable "
            "pipelines, evaluation stacks, and real-time interfaces around "
            f"{dominant_tag_text}, because those patterns tend to convert attention into "
            "sustained reuse."
        )

        signals = (
            f"Primary signals: dominant tags={dominant_tag_text}; repeated keywords="
            f"{repeated_keywords}; "
            f"selected repos={len(selected_repos)}."
        )

        return ForecastSection(
            headline="Where Things Are Headed",
            intro=(
                "These forecasts are heuristic, directional estimates based on the selected "
                "repositories "
                "and the wider scanned candidate set. They are not certainties."
            ),
            items=[
                ForecastItem(
                    title="Likely Near-Term Growth Clusters",
                    estimate=growth_estimate,
                    signals=signals,
                    implications=(
                        "Expect open-source effort to keep flowing toward the subdomains "
                        "with the strongest reuse and deployment story."
                    ),
                ),
                ForecastItem(
                    title="Likely Saturated Areas",
                    estimate=saturated_estimate,
                    signals=signals,
                    implications=(
                        "Repos that do not add workflow leverage or technical differentiation "
                        "are likely to be crowded out quickly."
                    ),
                ),
                ForecastItem(
                    title="Potential Breakout Project Archetypes",
                    estimate=breakout_estimate,
                    signals=signals,
                    implications=(
                        "The highest-upside projects are likely to combine infrastructure "
                        "depth with obvious end-user value."
                    ),
                ),
                ForecastItem(
                    title="Practical Implications",
                    estimate=implication_estimate,
                    signals=signals,
                    implications=(
                        "Track maintainers that are turning demos into repeatable systems, "
                        "not just raw models or isolated plugins."
                    ),
                ),
            ],
        )
