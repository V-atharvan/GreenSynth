"""
GreenSynth Analytics — SMTP Email Infrastructure & Notification Service

Provides a production-grade SMTP email delivery service with:
1. Jinja2 HTML and plain-text template rendering with automatic escaping.
2. Multipart/alternative email composition.
3. TLS (port 587) and SSL (port 465) secure transport.
4. Support for Gmail SMTP, local testing servers, and dev console mode.
5. Strict protection against credential and sensitive token leakage in logs.
"""

from __future__ import annotations

import logging
import os
import re
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Basic RFC 5322 compliant regex for recipient validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class EmailServiceError(Exception):
    """Raised when an email dispatch failure occurs."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class EmailService:
    """Production-grade email dispatch service with template support and robust error handling."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        template_dir = Path(__file__).resolve().parent.parent / "templates" / "email"
        
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.jinja_env = None

    def validate_recipient_email(self, email: str) -> str:
        """
        Validates the recipient email format.
        Raises EmailServiceError on malformed addresses.
        """
        if not email or not isinstance(email, str):
            raise EmailServiceError("Recipient email address cannot be empty.")

        cleaned = email.strip()
        _name, parsed_addr = parseaddr(cleaned)
        effective_addr = parsed_addr or cleaned

        if not EMAIL_REGEX.match(effective_addr):
            raise EmailServiceError(f"Invalid recipient email address format: '{effective_addr}'")

        return effective_addr

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Renders a Jinja2 template with dynamic context.
        Variables are automatically HTML-escaped for safety.
        """
        if not self.jinja_env:
            raise EmailServiceError(f"Email template engine not initialized (missing templates directory).")

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as exc:
            logger.error("Failed to render email template '%s': %s", template_name, exc)
            raise EmailServiceError(f"Failed to render email template '{template_name}'.", exc)

    def _create_smtp_connection(self) -> smtplib.SMTP | smtplib.SMTP_SSL:
        """
        Instantiates and returns an authenticated SMTP connection based on configuration.
        """
        timeout = self.settings.smtp_timeout
        server = None

        try:
            if self.settings.smtp_use_ssl:
                server = smtplib.SMTP_SSL(
                    host=self.settings.smtp_host,
                    port=self.settings.smtp_port,
                    timeout=timeout,
                )
            else:
                server = smtplib.SMTP(
                    host=self.settings.smtp_host,
                    port=self.settings.smtp_port,
                    timeout=timeout,
                )
                server.ehlo()
                if self.settings.smtp_use_tls:
                    server.starttls()
                    server.ehlo()

            if self.settings.smtp_username and self.settings.smtp_password:
                server.login(self.settings.smtp_username, self.settings.smtp_password)

            return server

        except Exception:
            if server:
                try:
                    server.quit()
                except Exception:
                    try:
                        server.close()
                    except Exception:
                        pass
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        reply_to: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> bool:
        """
        Dispatches a multipart/alternative email to the recipient.
        """
        valid_to = self.validate_recipient_email(to_email)

        # ── 1. Master Enable Check ────────────────────────────
        if not self.settings.email_enabled:
            logger.info("Email delivery is globally disabled. Skipping dispatch to %s.", valid_to)
            return True

        # ── 2. Development Console Mode ───────────────────────
        if self.settings.email_mode == "console":
            logger.info(
                "\n"
                "============================================================\n"
                "[CONSOLE EMAIL DISPATCH]\n"
                "To: %s\n"
                "Subject: %s\n"
                "From: %s <%s>\n"
                "------------------------------------------------------------\n"
                "%s\n"
                "============================================================",
                valid_to,
                subject,
                self.settings.smtp_from_name,
                self.settings.smtp_from_email,
                text_body,
            )
            return True

        # ── 3. Production SMTP Dispatch ───────────────────────
        # Ensure configuration is valid
        self.settings.validate_smtp_settings()

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((self.settings.smtp_from_name, self.settings.smtp_from_email))
        msg["To"] = valid_to

        if reply_to:
            valid_reply = self.validate_recipient_email(reply_to)
            msg["Reply-To"] = valid_reply

        if cc:
            valid_cc = [self.validate_recipient_email(addr) for addr in cc]
            msg["Cc"] = ", ".join(valid_cc)

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        server = None
        try:
            server = self._create_smtp_connection()
            recipients = [valid_to]
            if cc:
                recipients.extend([self.validate_recipient_email(addr) for addr in cc])
            if bcc:
                recipients.extend([self.validate_recipient_email(addr) for addr in bcc])

            server.send_message(msg, to_addrs=recipients)
            logger.info("Email with subject '%s' sent successfully to %s", subject, valid_to)
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error("SMTP authentication failed for user %s. Verify SMTP credentials.", self.settings.smtp_username)
            raise EmailServiceError("SMTP authentication failed. Please verify email credentials.", exc)

        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, ConnectionError) as exc:
            logger.error("SMTP connection error connecting to %s:%s", self.settings.smtp_host, self.settings.smtp_port)
            raise EmailServiceError("Unable to establish connection to SMTP mail server.", exc)

        except TimeoutError as exc:
            logger.error("SMTP connection timed out connecting to %s:%s", self.settings.smtp_host, self.settings.smtp_port)
            raise EmailServiceError("SMTP connection timed out.", exc)

        except smtplib.SMTPException as exc:
            logger.error("SMTP protocol exception occurred during email send: %s", exc)
            raise EmailServiceError("SMTP protocol error occurred during transmission.", exc)

        except Exception as exc:
            logger.error("Unexpected error occurred while dispatching email to %s: %s", valid_to, exc)
            raise EmailServiceError("Unexpected email transmission failure.", exc)

        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    try:
                        server.close()
                    except Exception:
                        pass

    async def send_group_invitation(
        self,
        to_email: str,
        recipient_name: str,
        group_name: str,
        project_name: str,
        project_code: str,
        leader_name: str,
        raw_token: str,
        expires_at: datetime,
    ) -> bool:
        """
        Renders the GreenSynth invitation templates and dispatches the email.
        Uses asyncio.to_thread to prevent blocking SMTP calls from freezing the event loop.
        """
        invitation_url = (
            f"{self.settings.frontend_base_url.rstrip('/')}/accept-invitation?token={raw_token}"
        )
        expires_str = expires_at.strftime("%B %d, %Y at %H:%M UTC")

        context = {
            "recipient_name": recipient_name,
            "group_name": group_name,
            "project_name": project_name,
            "project_code": project_code,
            "inviter_name": leader_name,
            "invitation_link": invitation_url,
            "expiration_time": expires_str,
            "subject": f"Invitation to Join Research Group '{group_name}' — GreenSynth Analytics",
        }

        subject = f"Invitation to Join a GreenSynth Research Group"

        html_body = self.render_template("invitation.html", context)
        text_body = self.render_template("invitation.txt", context)

        import asyncio
        return await asyncio.to_thread(
            self.send_email,
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

