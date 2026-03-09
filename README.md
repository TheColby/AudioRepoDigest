# AudioRepoDigest

Automated email digests of the most important audio, music, DSP, and audio-AI GitHub repos on a configurable schedule.

AudioRepoDigest discovers and ranks relevant GitHub repositories, then emails the **full report directly in the email body** (HTML + plaintext fallback).  
Default deployment is **GitHub Actions + SMTP**.

## What You Get

- Weekly-by-default scheduled report (`0 13 * * 1`, Monday morning UTC)
- Ranked sections:
  - Top Audio Repos
  - Top New Audio/Music Repos
  - Top Audio AI Repos
- Executive summary, table of contents, trend analysis, and directional forecasts
- Clickable inline repo links in the email body
- Exported run artifacts: HTML, Markdown, JSON

## Quick Start (GitHub Actions)

1. Push this repo to GitHub.
2. Add required Actions secrets.
3. Run workflow once in dry-run mode.
4. Run again with `dry_run=false` to send email.

Workflow file: [weekly-digest.yml](/Users/cleider/dev/AudioRepoDigest/.github/workflows/weekly-digest.yml)

## Required GitHub Secrets

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `REPORT_RECIPIENT_EMAIL`
- `REPORT_RECIPIENT_NAME`

Recommended:

- `AUDIOREPODIGEST_GITHUB_TOKEN`
- `REPORT_TIMEZONE`
- `REPORT_VERBOSITY` (`compact`, `standard`, `detailed`)
- `EMAIL_SUBJECT_PREFIX`

## Set Secrets From Command Line

Replace values where needed, then run:

```bash
gh secret set SMTP_HOST -R TheColby/AudioRepoDigest -b "smtp.gmail.com"
gh secret set SMTP_PORT -R TheColby/AudioRepoDigest -b "587"
gh secret set SMTP_USERNAME -R TheColby/AudioRepoDigest -b "colbyleider@gmail.com"
gh secret set SMTP_FROM -R TheColby/AudioRepoDigest -b "AudioRepoDigest <colbyleider@gmail.com>"
gh secret set REPORT_RECIPIENT_EMAIL -R TheColby/AudioRepoDigest -b "colbyleider@gmail.com"
gh secret set REPORT_RECIPIENT_NAME -R TheColby/AudioRepoDigest -b "Colby Leider"
```

Set SMTP password securely (prompted):

```bash
gh secret set SMTP_PASSWORD -R TheColby/AudioRepoDigest
```

Optional GitHub token:

```bash
gh secret set AUDIOREPODIGEST_GITHUB_TOKEN -R TheColby/AudioRepoDigest
```

Optional readability/behavior settings:

```bash
gh secret set REPORT_TIMEZONE -R TheColby/AudioRepoDigest -b "America/New_York"
gh secret set REPORT_VERBOSITY -R TheColby/AudioRepoDigest -b "compact"
gh secret set EMAIL_SUBJECT_PREFIX -R TheColby/AudioRepoDigest -b "[AudioRepoDigest]"
```

## Trigger Workflow

UI:

- Open [workflow page](https://github.com/TheColby/AudioRepoDigest/actions/workflows/weekly-digest.yml)
- Click `Run workflow`
- First run: `dry_run=true`
- Second run: `dry_run=false`

CLI:

```bash
gh workflow run weekly-digest.yml -R TheColby/AudioRepoDigest -f dry_run=true
gh run list -R TheColby/AudioRepoDigest --workflow weekly-digest.yml
```

Then send a live report:

```bash
gh workflow run weekly-digest.yml -R TheColby/AudioRepoDigest -f dry_run=false
```

## Report Verbosity

Use `REPORT_VERBOSITY`:

- `compact`: minimal cards, hidden detail blocks
- `standard`: concise cards + expandable details
- `detailed`: includes full metadata and expanded scoring details

## Local Development (Optional)

```bash
uv sync --group dev
uv run audiodigest validate-config
uv run audiodigest preview
uv run pytest
```

Local config files are ignored:

- `config.yaml`
- `config.local.yaml`

## Project Structure

```text
src/audiorepodigest/
  cli.py
  config.py
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

## License

MIT. See [LICENSE](/Users/cleider/dev/AudioRepoDigest/LICENSE).

