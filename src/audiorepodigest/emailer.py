from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from audiorepodigest.config import DigestSettings
from audiorepodigest.logging import get_logger
from audiorepodigest.models import DigestReport, RenderBundle

logger = get_logger(__name__)


class EmailSender:
    """Builds and sends multipart digest emails."""

    def __init__(self, settings: DigestSettings) -> None:
        self.settings = settings

    def build_message(
        self,
        report: DigestReport,
        render_bundle: RenderBundle,
        *,
        recipient_email: str | None = None,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        to_email = recipient_email or self.settings.report_recipient_email
        to_name = recipient_name or report.recipient_name

        message = EmailMessage()
        message["Subject"] = render_bundle.subject
        message["From"] = self.settings.smtp_from
        message["To"] = formataddr((to_name, to_email))
        message.set_content(render_bundle.text)
        message.add_alternative(render_bundle.html, subtype="html")
        return message

    def send_message(self, message: EmailMessage) -> None:
        try:
            if self.settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=30,
                    context=ssl.create_default_context(),
                ) as smtp:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=30,
                ) as smtp:
                    smtp.ehlo()
                    if self.settings.smtp_use_starttls:
                        smtp.starttls(context=ssl.create_default_context())
                        smtp.ehlo()
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                    smtp.send_message(message)
        except smtplib.SMTPAuthenticationError as exc:
            raise RuntimeError(self._build_authentication_error_message()) from exc
        logger.info("Email delivered to %s", message["To"])

    def send_render_bundle(
        self,
        report: DigestReport,
        render_bundle: RenderBundle,
        *,
        recipient_email: str | None = None,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        message = self.build_message(
            report,
            render_bundle,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
        )
        self.send_message(message)
        return message

    def _build_authentication_error_message(self) -> str:
        host = self.settings.smtp_host
        username = self.settings.smtp_username
        if host.lower() == "smtp.gmail.com":
            return (
                "SMTP authentication failed for smtp.gmail.com. "
                "Check the GitHub Actions secrets `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM`. "
                "For Gmail, `SMTP_USERNAME` should be the full Gmail address and `SMTP_PASSWORD` should be "
                "a current Google App Password created after enabling 2-Step Verification. "
                "If you pasted the App Password with spaces, AudioRepoDigest now strips them automatically, "
                "so a remaining failure usually means the App Password is expired, revoked, or tied to a "
                "different Google account than "
                f"`{username}`."
            )
        return (
            f"SMTP authentication failed for {host}. "
            "Check the GitHub Actions secrets `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM`."
        )
