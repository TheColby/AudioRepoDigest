# AudioRepoDigest

Automated email digests of the most important audio, music, DSP, and audio-AI GitHub repos on a configurable schedule.

AudioRepoDigest discovers and ranks relevant GitHub repositories, then emails the **full report directly in the email body** (HTML + plaintext fallback). Default deployment is **GitHub Actions + SMTP**.

## What You Get

- Weekly-by-default scheduled report (`0 20 * * 0`, Sunday afternoon default)
- Ranked sections:
  - Top Audio Repos
  - Top New Audio/Music Repos
  - Top Audio AI Repos
- Five deterministic, ecosystem-informed repository ideas to build each week
- Executive summary, table of contents, trend analysis, and directional forecasts
- Clickable inline repo links in the email body
- Exported run artifacts: HTML, Markdown, JSON

## Quick Start (GitHub Actions)

1. Push this repo to GitHub.
2. Add required Actions secrets.
3. Run workflow once in dry-run mode.
4. Run again with `dry_run=false` to send email.

Workflow file: [weekly-digest.yml](/Users/cleider/dev/AudioRepoDigest/.github/workflows/weekly-digest.yml)
Heartbeat workflow: [email-heartbeat.yml](/Users/cleider/dev/AudioRepoDigest/.github/workflows/email-heartbeat.yml)

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
gh secret set SMTP_USERNAME -R TheColby/AudioRepoDigest -b "your.email@gmail.com"
gh secret set SMTP_FROM -R TheColby/AudioRepoDigest -b "AudioRepoDigest <colbyleider@gmail.com>"
gh secret set REPORT_RECIPIENT_EMAIL -R TheColby/AudioRepoDigest -b "your.email@gmail.com"
gh secret set REPORT_RECIPIENT_NAME -R TheColby/AudioRepoDigest -b "Your Name"
```

Set SMTP password securely (prompted):

```bash
gh secret set SMTP_PASSWORD -R TheColby/AudioRepoDigest
```

Gmail note:

- `SMTP_USERNAME` should be your full Gmail address.
- `SMTP_PASSWORD` should be a Google App Password, not your normal Gmail password.
- If you paste the App Password with spaces, AudioRepoDigest strips them automatically for Gmail.
- A `535 5.7.8 Username and Password not accepted` error usually means the App Password was revoked, expired, or created under a different Google account.

Optional GitHub token:

```bash
gh secret set AUDIOREPODIGEST_GITHUB_TOKEN -R TheColby/AudioRepoDigest
```

Optional readability/behavior settings:

```bash
gh secret set REPORT_TIMEZONE -R TheColby/AudioRepoDigest -b "America/New_York"
gh secret set REPORT_VERBOSITY -R TheColby/AudioRepoDigest -b "compact"
gh secret set EMAIL_SUBJECT_PREFIX -R TheColby/AudioRepoDigest -b "[COLBY AUDIO DIGEST]"
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

Manual heartbeat:

```bash
gh workflow run email-heartbeat.yml -R TheColby/AudioRepoDigest
gh run list -R TheColby/AudioRepoDigest --workflow email-heartbeat.yml
```

Multiple recipients:

- `REPORT_RECIPIENT_EMAIL` can be a comma-separated list such as `colby@leider.org, colbyleider@gmail.com`
- AudioRepoDigest sends a separate email to each listed recipient

## Report Verbosity

Use `REPORT_VERBOSITY`:

- `compact`: minimal cards, hidden detail blocks
- `standard`: concise cards + expandable details
- `detailed`: includes full metadata and expanded scoring details

## Weekly Repo Ideas

Every digest includes `10 Repo Ideas to Build This Week`. The ideas are generated without an LLM: the system maps dominant weekly tags and gaps in the scanned ecosystem to practical project archetypes, with a recommended first release and the relevant weekly signal.

Set `INCLUDE_REPO_IDEAS=false` to disable this section.

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
