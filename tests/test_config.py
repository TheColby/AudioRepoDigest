from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from audiorepodigest.config import load_settings
from audiorepodigest.models import ReportFrequency


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "GITHUB_TOKEN": "ghp_test",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "sender@example.com",
        "SMTP_PASSWORD": "secret",
        "SMTP_FROM": "AudioRepoDigest <sender@example.com>",
        "REPORT_RECIPIENT_EMAIL": "colbyleider@gmail.com",
        "REPORT_RECIPIENT_NAME": "Colby Leider",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_load_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("REPORT_FREQUENCY", "weekly")
    settings = load_settings()
    assert settings.report_frequency is ReportFrequency.WEEKLY
    assert settings.report_recipient_email == "colbyleider@gmail.com"
    assert settings.effective_cron == "0 13 * * 1"


def test_load_settings_merges_yaml_and_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "smtp.override.example.com")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "report_frequency": "monthly",
                "smtp_host": "smtp.from.yaml",
                "top_n_main": 22,
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)
    assert settings.smtp_host == "smtp.override.example.com"
    assert settings.report_frequency is ReportFrequency.MONTHLY
    assert settings.top_n_main == 22


def test_custom_frequency_requires_cron(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("REPORT_FREQUENCY", "custom")
    monkeypatch.delenv("REPORT_CRON", raising=False)
    with pytest.raises(ValidationError):
        load_settings()
