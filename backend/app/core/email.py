"""Email helpers for outbound notifications."""
from __future__ import annotations

from email.message import EmailMessage
import smtplib
from typing import Iterable

from app.core.config import settings


def _parse_recipients(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [entry.strip() for entry in raw.split(",") if entry.strip()]


def get_admin_recipients() -> list[str]:
    return _parse_recipients(settings.admin_notify_emails)


def send_email(subject: str, body: str, *, recipients: Iterable[str]) -> None:
    if not settings.smtp_enabled:
        return

    recipients = list(recipients)
    if not recipients:
        return

    if not settings.smtp_host:
        return

    sender = settings.smtp_from or settings.smtp_username
    if not sender:
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)
