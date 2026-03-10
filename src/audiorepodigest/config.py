from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, ClassVar
from zoneinfo import ZoneInfo

from croniter import croniter
from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict, YamlConfigSettingsSource

from audiorepodigest.models import ReportFrequency, ReportVerbosity


class DigestSettings(BaseSettings):
    """Runtime configuration for AudioRepoDigest."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    _config_path: ClassVar[Path | None] = None

    github_token: str = Field(validation_alias="GITHUB_TOKEN")

    smtp_host: str = Field(validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_username: str = Field(validation_alias="SMTP_USERNAME")
    smtp_password: str = Field(validation_alias="SMTP_PASSWORD")
    smtp_from: str = Field(validation_alias="SMTP_FROM")
    smtp_use_starttls: bool = Field(default=True, validation_alias="SMTP_USE_STARTTLS")
    smtp_use_ssl: bool = Field(default=False, validation_alias="SMTP_USE_SSL")

    report_recipient_email: str = Field(validation_alias="REPORT_RECIPIENT_EMAIL")
    report_recipient_name: str = Field(
        default="Colby Leider", validation_alias="REPORT_RECIPIENT_NAME"
    )
    report_frequency: ReportFrequency = Field(
        default=ReportFrequency.WEEKLY,
        validation_alias="REPORT_FREQUENCY",
    )
    report_cron: str | None = Field(default=None, validation_alias="REPORT_CRON")
    report_timezone: str = Field(default="America/New_York", validation_alias="REPORT_TIMEZONE")
    report_lookback_days: int = Field(default=7, validation_alias="REPORT_LOOKBACK_DAYS")
    report_verbosity: ReportVerbosity = Field(
        default=ReportVerbosity.STANDARD,
        validation_alias="REPORT_VERBOSITY",
    )

    top_n_main: int = Field(default=10, validation_alias="TOP_N_MAIN")
    top_n_new: int = Field(default=7, validation_alias="TOP_N_NEW")
    top_n_audio_ai: int = Field(default=7, validation_alias="TOP_N_AUDIO_AI")

    include_summaries: bool = Field(default=True, validation_alias="INCLUDE_SUMMARIES")
    include_honorable_mentions: bool = Field(
        default=True,
        validation_alias="INCLUDE_HONORABLE_MENTIONS",
    )
    include_trend_analysis: bool = Field(
        default=True,
        validation_alias="INCLUDE_TREND_ANALYSIS",
    )
    include_forecasts: bool = Field(default=True, validation_alias="INCLUDE_FORECASTS")
    suppress_honorable_mention_duplicates: bool = Field(
        default=True,
        validation_alias="SUPPRESS_HONORABLE_MENTION_DUPLICATES",
    )

    max_candidates_to_scan: int = Field(default=180, validation_alias="MAX_CANDIDATES_TO_SCAN")
    github_search_window_days: int = Field(default=21, validation_alias="GITHUB_SEARCH_WINDOW_DAYS")
    readme_fallback_limit: int = Field(default=6, validation_alias="README_FALLBACK_LIMIT")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    email_subject_prefix: str = Field(
        default="[AudioRepoDigest]", validation_alias="EMAIL_SUBJECT_PREFIX"
    )
    allowlist_topics: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="ALLOWLIST_TOPICS",
    )
    blocklist_terms: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="BLOCKLIST_TERMS",
    )

    output_html_path: Path | None = Field(default=None, validation_alias="OUTPUT_HTML_PATH")
    output_markdown_path: Path | None = Field(default=None, validation_alias="OUTPUT_MARKDOWN_PATH")
    output_json_path: Path | None = Field(default=None, validation_alias="OUTPUT_JSON_PATH")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        sources: list[Any] = [init_settings, env_settings, dotenv_settings]
        if cls._config_path is not None:
            sources.append(YamlConfigSettingsSource(settings_cls, yaml_file=cls._config_path))
        sources.append(file_secret_settings)
        return tuple(sources)

    @field_validator("allowlist_topics", "blocklist_terms", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("report_timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        ZoneInfo(value)
        return value

    @field_validator("report_cron")
    @classmethod
    def _validate_cron(cls, value: str | None, info: ValidationInfo) -> str | None:
        frequency = info.data.get("report_frequency")
        if frequency == ReportFrequency.CUSTOM and not value:
            raise ValueError("REPORT_CRON must be set when REPORT_FREQUENCY=custom.")
        if value:
            if not croniter.is_valid(value):
                raise ValueError(f"Invalid cron expression: {value}")
        return value

    @model_validator(mode="after")
    def _validate_transport_flags(self) -> DigestSettings:
        if self.smtp_use_starttls and self.smtp_use_ssl:
            raise ValueError("SMTP_USE_STARTTLS and SMTP_USE_SSL cannot both be enabled.")
        return self

    @property
    def effective_cron(self) -> str:
        if self.report_cron:
            return self.report_cron
        if self.report_frequency is ReportFrequency.DAILY:
            return "0 13 * * *"
        if self.report_frequency is ReportFrequency.MONTHLY:
            return "0 13 1 * *"
        if self.report_frequency is ReportFrequency.CUSTOM:
            return "0 13 * * 1"
        return "0 20 * * 0"


def load_settings(
    config_path: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> DigestSettings:
    previous_path = DigestSettings._config_path
    DigestSettings._config_path = config_path
    try:
        return DigestSettings(**(overrides or {}))
    finally:
        DigestSettings._config_path = previous_path
