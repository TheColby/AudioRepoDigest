from __future__ import annotations

import smtplib
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
        if self.settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=30,
            ) as smtp:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=30,
            ) as smtp:
                if self.settings.smtp_use_starttls:
                    smtp.starttls()
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message)
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
