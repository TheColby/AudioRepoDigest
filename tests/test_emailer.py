from __future__ import annotations

import smtplib

import pytest

from audiorepodigest.emailer import EmailSender
from audiorepodigest.models import DigestReport, RenderBundle


def test_email_message_contains_text_and_html_alternatives(
    settings, rendered_report_bundle
) -> None:
    report, bundle = rendered_report_bundle
    message = EmailSender(settings).build_message(report, bundle)

    assert message["Subject"] == bundle.subject
    assert message["To"] == "Colby Leider <colbyleider@gmail.com>"
    assert message["Reply-To"] == settings.smtp_from
    assert message["Auto-Submitted"] == "auto-generated"
    assert message["X-Mailer"] == "AudioRepoDigest"
    assert message["Message-ID"] is not None
    assert message["Date"] is not None
    assert message.is_multipart()
    payload = message.get_payload()
    assert payload[0].get_content_type() == "text/plain"
    assert payload[1].get_content_type() == "text/html"


def test_gmail_auth_error_has_actionable_message(
    monkeypatch: pytest.MonkeyPatch, settings
) -> None:
    settings.smtp_host = "smtp.gmail.com"
    settings.smtp_username = "colbyleider@gmail.com"
    settings.smtp_password = "abcdefghijklmnop"

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self) -> FakeSMTP:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def ehlo(self) -> None:
            return None

        def starttls(self, context=None) -> None:
            return None

        def login(self, username: str, password: str) -> None:
            raise smtplib.SMTPAuthenticationError(
                535,
                b"5.7.8 Username and Password not accepted.",
            )

        def send_message(self, message) -> None:
            return None

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    sender = EmailSender(settings)
    message = sender.build_message(
        DigestReport.model_construct(
            title="Colby's AudioRepoDigest",
            subtitle="Test digest",
            generated_at=None,
            period=None,
            recipient_name="Colby Leider",
            executive_summary="",
            scanned_candidate_count=0,
            selected_repo_count=0,
            version="0.1.0",
        ),
        RenderBundle(
            subject="Test",
            text="Plain",
            html="<p>HTML</p>",
            markdown=None,
            json_payload={},
        ),
    )

    with pytest.raises(RuntimeError, match="Google App Password"):
        sender.send_message(message)


def test_simple_message_contains_standard_headers(settings) -> None:
    message = EmailSender(settings).build_simple_message(
        subject="[AudioRepoDigest] Heartbeat",
        text="Heartbeat",
        html="<p>Heartbeat</p>",
    )

    assert message["Subject"] == "[AudioRepoDigest] Heartbeat"
    assert message["To"] == "Colby Leider <colbyleider@gmail.com>"
    assert message["Reply-To"] == settings.smtp_from
    assert message["X-Mailer"] == "AudioRepoDigest"
    assert message.is_multipart()
