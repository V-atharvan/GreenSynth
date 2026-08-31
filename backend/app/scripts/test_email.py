"""
GreenSynth Analytics — Manual SMTP Verification Script

Allows developers to perform a controlled manual verification of the SMTP email service.
Reads credentials strictly from the environment/.env without hardcoding.

Usage:
    python -m app.scripts.test_email [optional_recipient_email]
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from app.core.config import get_settings
from app.services.email_service import EmailService


def main() -> None:
    settings = get_settings()
    recipient = sys.argv[1] if len(sys.argv) > 1 else (settings.smtp_from_email or "v.atharvan@gmail.com")

    print("============================================================")
    print("GreenSynth Analytics — SMTP Email Verification")
    print(f"Host: {settings.smtp_host}:{settings.smtp_port} (TLS={settings.smtp_use_tls}, SSL={settings.smtp_use_ssl})")
    print(f"Sender: {settings.smtp_from_name} <{settings.smtp_from_email}>")
    print(f"Recipient: {recipient}")
    print(f"Mode: {settings.email_mode}")
    print("============================================================")

    service = EmailService(settings)
    subject = "[GreenSynth Test] SMTP Configuration Verification"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    text_body = f"""Hello,

This is an automated test email from the GreenSynth Analytics Research Platform.
Sent at: {now_str}

SMTP infrastructure is functioning correctly.

Regards,
GreenSynth Analytics
"""

    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #1e293b; padding: 20px;">
    <h2 style="color: #064e3b;">GreenSynth Analytics — SMTP Verification</h2>
    <p>This is an automated verification email confirming that the GreenSynth SMTP email service is functioning properly.</p>
    <p><strong>Timestamp:</strong> {now_str}</p>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
    <p style="font-size: 12px; color: #64748b;">GreenSynth Analytics — Semiconductor Nanomaterials Research Platform</p>
</body>
</html>
"""

    try:
        success = service.send_email(
            to_email=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        if success:
            print(f"SUCCESS: Test email successfully processed for {recipient}.")
        else:
            print(f"FAILURE: Test email dispatch returned False.")
    except Exception as exc:
        print(f"ERROR: Email dispatch failed: {exc}")


if __name__ == "__main__":
    main()
