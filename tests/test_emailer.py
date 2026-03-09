from __future__ import annotations

from audiorepodigest.emailer import EmailSender


def test_email_message_contains_text_and_html_alternatives(
    settings, rendered_report_bundle
) -> None:
    report, bundle = rendered_report_bundle
    message = EmailSender(settings).build_message(report, bundle)

    assert message["Subject"] == bundle.subject
    assert message["To"] == "Colby Leider <colbyleider@gmail.com>"
    assert message.is_multipart()
    payload = message.get_payload()
    assert payload[0].get_content_type() == "text/plain"
    assert payload[1].get_content_type() == "text/html"
