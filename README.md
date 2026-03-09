# AudioRepoDigest

Automated email digests of the most important audio, music, DSP, and audio-AI GitHub repos on a configurable schedule.

AudioRepoDigest scans GitHub for relevant repositories across audio engineering, music software, DSP, MIR, speech, plugins, synthesis, spatial audio, and audio-AI. It classifies candidates with transparent heuristics, ranks the strongest repos for the reporting window, renders a polished digest, and sends the full report directly in the email body through SMTP.

## Why this project exists

The audio GitHub ecosystem is broad and fragmented. Interesting work spans classic DSP, plugins, creator tooling, speech pipelines, generative audio, source separation, MIR, room acoustics, and developer infrastructure. AudioRepoDigest turns that sprawl into a recurring intelligence report with ranked sections, an executive summary, a table of contents, deep trend analysis, and best-effort directional forecasts.

## Core features

- Weekly-by-default GitHub intelligence reporting with `daily`, `weekly`, `monthly`, and custom cron support.
- Full report rendered directly in the email body as HTML plus plaintext fallback.
- Clickable inline hyperlinks for every ranked repository.
- Top sections for:
  - Top Audio Repos for the period
  - Top New Audio/Music Repos for the period
  - Top Audio AI Repos for the period
- Executive summary near the top of the email.
- Table of contents at the top of the email.
- Comprehensive trend analysis at the end of the report.
- Best-effort forecasts labeled as heuristic and directional.
- CLI for previewing, exporting, validating config, listing candidates, explaining scores, and sending test emails.
- GitHub Actions workflow for scheduled execution every Monday morning by default.
- Environment-variable configuration with optional YAML overlay.

## Important email behavior

AudioRepoDigest is explicitly email-first.

The emailed report is rendered directly in the email body with inline hyperlinks, not as a link-out button, not as an attachment, and not as a placeholder CTA. The HTML body contains the full report and the plaintext alternative contains the same core content for clients that do not render HTML.

## Repo description

Use this repo description on GitHub:

> Automated email digests of the most important audio, music, DSP, and audio-AI GitHub repos on a configurable schedule.

## Default deployment choice

The primary and most polished deployment story is:

- GitHub Actions + SMTP

The included workflow is scheduled for weekly Monday morning runs using the default cron:

- `0 13 * * 1`

That is `13:00 UTC` every Monday and is easy to customize.

## Architecture

```text
src/audiorepodigest/
  cli.py
  config.py
  github_client.py
  discovery.py
  classification.py
  ranking.py
  trends.py
  forecasting.py
  reporting.py
  emailer.py
  pipeline.py
  templates/
```

Pipeline summary:

1. Query GitHub using multiple targeted search families.
2. Deduplicate and classify candidates with heuristic relevance scoring.
3. Rank repos for the main, new, and audio-AI sections.
4. Generate the executive summary, trend analysis, and forecasts.
5. Render HTML email, plaintext fallback, markdown preview, and JSON export.
6. Send the report through SMTP or preview it locally.

## Installation

### Prerequisites

- Python 3.12+
- `uv`
- A GitHub token with enough quota for repository search
- An SMTP account that can send mail from your chosen sender

### Setup

```bash
uv sync --group dev
cp .env.example .env
```

Fill in at least:

- `GITHUB_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `REPORT_RECIPIENT_EMAIL`
- `REPORT_RECIPIENT_NAME`
- `REPORT_FREQUENCY`
- `REPORT_TIMEZONE`

Optional:

- Use `config.example.yaml` as a YAML overlay if you prefer file-based settings.
- Environment variables override YAML values.

## Quick start

Validate configuration:

```bash
uv run audiodigest validate-config
```

Render a local preview without sending:

```bash
uv run audiodigest preview
```

Render and send the digest:

```bash
uv run audiodigest run
```

Send a test message to an alternate recipient:

```bash
uv run audiodigest send-test-email --recipient-email you@example.com --recipient-name "Test Recipient"
```

## CLI commands

```bash
uv run audiodigest run
uv run audiodigest preview
uv run audiodigest send-test-email
uv run audiodigest validate-config
uv run audiodigest list-candidates
uv run audiodigest explain-score owner/repo
uv run audiodigest trends
uv run audiodigest export
```

Useful examples:

```bash
uv run audiodigest preview --start-date 2026-03-02 --end-date 2026-03-08
uv run audiodigest list-candidates --limit 40
uv run audiodigest explain-score openai/jukebox
uv run audiodigest export --output-html artifacts/preview.html --output-json artifacts/preview.json
uv run audiodigest run --dry-run
```

## Configuration

Settings are loaded from:

1. CLI overrides
2. Environment variables
3. `.env`
4. Optional YAML config file

Main configuration fields:

- `GITHUB_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `REPORT_RECIPIENT_EMAIL`
- `REPORT_RECIPIENT_NAME`
- `REPORT_FREQUENCY`
- `REPORT_CRON`
- `REPORT_TIMEZONE`
- `TOP_N_MAIN`
- `TOP_N_NEW`
- `TOP_N_AUDIO_AI`

Useful optional fields:

- `INCLUDE_HONORABLE_MENTIONS`
- `INCLUDE_TREND_ANALYSIS`
- `INCLUDE_FORECASTS`
- `MAX_CANDIDATES_TO_SCAN`
- `GITHUB_SEARCH_WINDOW_DAYS`
- `EMAIL_SUBJECT_PREFIX`
- `ALLOWLIST_TOPICS`
- `BLOCKLIST_TERMS`
- `OUTPUT_HTML_PATH`
- `OUTPUT_MARKDOWN_PATH`
- `OUTPUT_JSON_PATH`

For `REPORT_FREQUENCY=custom`, set `REPORT_CRON` and optionally tune `REPORT_LOOKBACK_DAYS` so the digest window matches your schedule.

## GitHub Actions setup

The repository includes [.github/workflows/weekly-digest.yml](/Users/cleider/dev/AudioRepoDigest/.github/workflows/weekly-digest.yml) with:

- `schedule` for weekly Monday morning execution
- `workflow_dispatch` for manual runs
- artifact upload for HTML, markdown, and JSON previews

Recommended GitHub Secrets:

- `AUDIOREPODIGEST_GITHUB_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `REPORT_RECIPIENT_EMAIL`
- `REPORT_RECIPIENT_NAME`
- `REPORT_TIMEZONE`
- `EMAIL_SUBJECT_PREFIX`

The workflow already defaults the schedule to Monday morning. To customize the schedule, change either:

- the cron under `on.schedule`
- or `REPORT_CRON` if you also use custom local scheduling conventions

### GitHub Actions only runbook

If you are running this project only via GitHub Actions, this is the fastest path:

1. Push the repository (already done if your branch is on GitHub).
2. In GitHub, open `Settings -> Secrets and variables -> Actions -> Repository secrets`.
3. Add required secrets:
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `SMTP_FROM`
   - `REPORT_RECIPIENT_EMAIL`
   - `REPORT_RECIPIENT_NAME`
4. Add optional but recommended secrets:
   - `AUDIOREPODIGEST_GITHUB_TOKEN` (improves GitHub API quota)
   - `REPORT_TIMEZONE` (`America/New_York` for Colby)
   - `EMAIL_SUBJECT_PREFIX` (defaults to `[AudioRepoDigest]`)
5. Open `Actions -> AudioRepoDigest -> Run workflow` and run once with `dry_run=true`.
6. Inspect generated artifacts (`digest.html`, `digest.md`, `digest.json`) in the workflow run.
7. Run again with `dry_run=false` to send the first live email.

What has already been prepared in this repo for Actions:

- Weekly default schedule: Monday mornings (`0 13 * * 1`).
- Manual `workflow_dispatch` execution with optional recipient/date overrides.
- Preflight secret validation step that fails fast with clear missing-key errors.
- Concurrency control to avoid overlapping digest runs.
- Artifact upload configured for every run.

Local-only config safety:

- `config.yaml` and `config.local.yaml` are git-ignored and are not used by the Actions workflow unless you explicitly change the workflow to pass `--config`.

## SMTP notes

AudioRepoDigest expects a normal SMTP relay. Gmail, Mailgun, Postmark SMTP, Fastmail, or a corporate SMTP gateway all work as long as you set the right host, port, username, password, and TLS mode.

Recommended first path:

- `SMTP_PORT=587`
- `SMTP_USE_STARTTLS=true`
- `SMTP_USE_SSL=false`

If your provider requires implicit TLS, use:

- `SMTP_PORT=465`
- `SMTP_USE_STARTTLS=false`
- `SMTP_USE_SSL=true`

## Scheduling outside GitHub Actions

GitHub Actions is the primary deployment path, but local or server scheduling is straightforward.

Example cron entry:

```cron
0 9 * * 1 cd /path/to/AudioRepoDigest && /usr/bin/env uv run audiodigest run >> /var/log/audiorepodigest.log 2>&1
```

You can also wrap the CLI in `systemd`, `launchd`, or another scheduler if you want the digest to run outside GitHub-hosted infrastructure.

## How scoring works

### Relevance classification

The v1 classifier is heuristic and transparent. It scores:

- repo name
- description
- GitHub topics
- README text for borderline cases

Tag buckets include:

- `general_audio`
- `audio_ai`
- `music_software`
- `dsp`
- `speech`
- `spatial_audio`
- `plugins`
- `synthesis`
- `mir`
- `beamforming`
- `acoustics`
- `developer_tooling`

False positives are reduced with configurable negative terms such as `car audio`, `audiobook`, or bot-like consumer repos.

### Ranking

The three ranked sections use different heuristics:

- `Top Audio Repos`: relevance, stars, forks, watchers, recent pushes, recent updates, and baseline popularity.
- `Top New Audio/Music Repos`: creation inside the reporting window, early traction, velocity, relevance, and sustained activity.
- `Top Audio AI Repos`: audio-AI specificity, overall relevance, traction, recent activity, and technical distinctiveness.

Use `audiodigest explain-score owner/repo` to inspect category-by-category score components.

## Trend analysis

The trend engine is deterministic and does not depend on proprietary LLM APIs.

It aggregates:

- selected repo tag buckets
- repeated keywords from names, topics, and descriptions
- inferred segments such as research, tooling, productization, developer tooling, creative tools, and spatial audio
- underrepresented sectors compared with the broader candidate pool

The result is a structured narrative that comments on:

- dominant technical themes
- developer attention patterns
- commercialization versus experimentation
- audio-AI versus traditional DSP/plugin work
- notable gaps

## Forecasting

The forecast section is intentionally labeled as:

- heuristic
- directional
- best-effort
- not a certainty

It estimates:

- near-term growth clusters
- likely saturated areas
- potential breakout archetypes
- practical implications for maintainers, engineers, and founders

## Sample report excerpt

```text
AudioRepoDigest
Report period: 2026-03-02 to 2026-03-08

EXECUTIVE SUMMARY
This weekly digest scanned 143 relevant GitHub candidates and selected 24 repositories worth immediate review.
The most important names this cycle were owner/audio-core, owner/neural-audio-lab, and owner/new-midi-stack.

TOP AUDIO REPOS
1. owner/audio-core
URL: https://github.com/owner/audio-core
Stats: 3200 stars, 310 forks, 18 open issues
Why included: 3200 stars; 310 forks; tags: dsp, plugins, synthesis; active code pushes during the period
```

## Output artifacts

The renderer can write:

- HTML preview
- Markdown preview
- JSON export

These are controlled by:

- `OUTPUT_HTML_PATH`
- `OUTPUT_MARKDOWN_PATH`
- `OUTPUT_JSON_PATH`

## Testing

Run the test suite:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
uv run ruff format --check .
```

## Limitations

- GitHub search does not expose a clean, low-cost star-delta history for every repo, so momentum is estimated heuristically from current traction plus recent activity.
- Search recall depends on keyword and topic quality; niche repos with weak metadata can still be missed.
- Trend analysis and forecasts are deterministic heuristics, not market predictions.
- SMTP delivery quality depends on sender reputation and provider configuration.

## Roadmap

- Better query families and per-domain weighting.
- Optional historical snapshots for cleaner delta tracking.
- Category-specific duplicate suppression policies.
- Optional CSV export and richer score introspection.
- Better README-aware classification limits and caching.
- Comparative period-over-period reporting.

## License

This project is licensed under the MIT License. See [LICENSE](/Users/cleider/dev/AudioRepoDigest/LICENSE).

## Immediate usability

After cloning this repo, the intended path is:

1. Set secrets or `.env` values.
2. Run `uv sync --group dev`.
3. Run `uv run audiodigest preview`.
4. Enable the included GitHub Actions workflow or schedule the CLI locally.

That is enough to get the first production-style digest out without adding a database or a dashboard.
