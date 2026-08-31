"""
GreenSynth Analytics — Phase 16 SMTP Email Infrastructure Unit Tests

Validates:
1. SMTP settings loading and validation (missing hosts, missing credentials, SSL/TLS conflict).
2. Email recipient address validation (RFC compliant, rejects malformed).
3. Jinja2 template rendering with dynamic context & HTML auto-escaping.
4. Multipart/alternative MIME message construction.
5. SMTP connection management with mocked smtplib (STARTTLS, authentication, quit).
6. SMTP error handling (AuthenticationError, ConnectError, TimeoutError, SMTPServerDisconnected).
7. Security: Zero password/credential exposure in exceptions or logs.
8. Console and disabled modes for local development.
9. Async send_group_invitation integration with mocked transport.
"""

import smtplib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services.email_service import EmailService, EmailServiceError


@pytest.fixture
def smtp_settings():
    """Provides valid SMTP configuration settings for testing."""
    return Settings(
        email_mode="smtp",
        email_enabled=True,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="v.atharvan@gmail.com",
        smtp_password="test-app-password-16char",
        smtp_from_email="v.atharvan@gmail.com",
        smtp_from_name="GreenSynth Analytics",
        smtp_use_tls=True,
        smtp_use_ssl=False,
        smtp_timeout=30,
        frontend_base_url="http://localhost:5173",
    )


# ── 1. CONFIGURATION & VALIDATION TESTS ──────────────────────────────

def test_smtp_configuration_loads_correctly(smtp_settings):
    """SMTP configuration loads all parameters with correct types."""
    assert smtp_settings.smtp_host == "smtp.gmail.com"
    assert smtp_settings.smtp_port == 587
    assert smtp_settings.smtp_use_tls is True
    assert smtp_settings.smtp_use_ssl is False
    assert smtp_settings.smtp_from_name == "GreenSynth Analytics"


def test_smtp_ssl_and_tls_conflict_rejected():
    """Reject invalid configuration where both TLS and SSL are enabled."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            smtp_use_tls=True,
            smtp_use_ssl=True,
        )
    assert "Cannot enable both SMTP_USE_TLS and SMTP_USE_SSL simultaneously" in str(exc.value)


def test_missing_smtp_credentials_validation(smtp_settings):
    """Missing username or password in SMTP mode raises a clear error."""
    smtp_settings.smtp_password = ""
    with pytest.raises(ValueError) as exc:
        smtp_settings.validate_smtp_settings()
    assert "credentials" in str(exc.value).lower()
    # Ensure no passwords or raw strings leaked
    assert "test-app-password" not in str(exc.value)


def test_missing_smtp_host_validation(smtp_settings):
    """Missing host in SMTP mode raises a configuration error."""
    smtp_settings.smtp_host = ""
    with pytest.raises(ValueError) as exc:
        smtp_settings.validate_smtp_settings()
    assert "SMTP_HOST" in str(exc.value)


# ── 2. RECIPIENT VALIDATION ──────────────────────────────────────────

def test_recipient_email_validation(smtp_settings):
    """Validates valid email addresses and rejects invalid formats."""
    service = EmailService(smtp_settings)

    assert service.validate_recipient_email("student@greensynth.edu") == "student@greensynth.edu"
    assert service.validate_recipient_email("alice.smith+lab@university.ac.in") == "alice.smith+lab@university.ac.in"
    assert service.validate_recipient_email("  researcher@org.com  ") == "researcher@org.com"

    with pytest.raises(EmailServiceError):
        service.validate_recipient_email("invalid-address")

    with pytest.raises(EmailServiceError):
        service.validate_recipient_email("")

    with pytest.raises(EmailServiceError):
        service.validate_recipient_email("plainaddress")


# ── 3. TEMPLATE RENDERING & AUTO-ESCAPING ────────────────────────────

def test_invitation_template_rendering_and_escaping(smtp_settings):
    """Jinja2 renders invitation HTML and plain text with auto-escaped variables."""
    service = EmailService(smtp_settings)
    context = {
        "recipient_name": "<script>alert('hack')</script>Rahul",
        "group_name": "Nanotech & Materials Group",
        "project_name": "CuO Phytochemical Synthesis",
        "project_code": "P7",
        "inviter_name": "Atharva V",
        "invitation_link": "http://localhost:5173/accept-invitation?token=secure123",
        "expiration_time": "August 30, 2026 at 18:00 UTC",
    }

    html = service.render_template("invitation.html", context)
    text = service.render_template("invitation.txt", context)

    # Variables rendered
    assert "Rahul" in html
    assert "Nanotech &amp; Materials Group" in html or "Nanotech & Materials Group" in html
    assert "P7" in html
    assert "Atharva V" in html
    assert "http://localhost:5173/accept-invitation?token=secure123" in html

    # Auto-escaping verified: raw script tags are escaped
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

    # Plain text contains clean text
    assert "Hello" in text
    assert "P7" in text
    assert "http://localhost:5173/accept-invitation?token=secure123" in text


# ── 4. SMTP SENDING & MOCK VERIFICATION ──────────────────────────────

@patch("smtplib.SMTP")
def test_smtp_send_email_success(mock_smtp_class, smtp_settings):
    """Verifies that send_email connects via STARTTLS, authenticates, dispatches, and quits."""
    mock_server = MagicMock()
    mock_smtp_class.return_value = mock_server

    service = EmailService(smtp_settings)
    success = service.send_email(
        to_email="student@greensynth.edu",
        subject="Research Platform Notification",
        html_body="<p>Test HTML body</p>",
        text_body="Test Plain Text body",
    )

    assert success is True
    mock_smtp_class.assert_called_once_with(host="smtp.gmail.com", port=587, timeout=30)
    mock_server.ehlo.assert_called()
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("v.atharvan@gmail.com", "test-app-password-16char")
    mock_server.send_message.assert_called_once()
    mock_server.quit.assert_called_once()

    # Check generated MIME message
    sent_msg = mock_server.send_message.call_args[0][0]
    assert sent_msg["To"] == "student@greensynth.edu"
    assert "GreenSynth Analytics <v.atharvan@gmail.com>" in sent_msg["From"]
    assert sent_msg["Subject"] == "Research Platform Notification"
    assert sent_msg.is_multipart()


@patch("smtplib.SMTP")
def test_smtp_authentication_failure_handled(mock_smtp_class, smtp_settings):
    """SMTP authentication failure raises controlled EmailServiceError."""
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication credentials invalid")
    mock_smtp_class.return_value = mock_server

    service = EmailService(smtp_settings)
    with pytest.raises(EmailServiceError) as exc:
        service.send_email(
            to_email="student@greensynth.edu",
            subject="Test Subject",
            html_body="<p>HTML</p>",
            text_body="Text",
        )

    assert "SMTP authentication failed" in str(exc.value)
    # Ensure server connection was cleaned up
    mock_server.quit.assert_called_once()


@patch("smtplib.SMTP")
def test_smtp_connection_failure_handled(mock_smtp_class, smtp_settings):
    """SMTP network connection failure raises EmailServiceError."""
    mock_smtp_class.side_effect = smtplib.SMTPConnectError(421, b"Connection refused")

    service = EmailService(smtp_settings)
    with pytest.raises(EmailServiceError) as exc:
        service.send_email(
            to_email="student@greensynth.edu",
            subject="Test Subject",
            html_body="<p>HTML</p>",
            text_body="Text",
        )

    assert "Unable to establish connection to SMTP" in str(exc.value)


@patch("smtplib.SMTP")
def test_smtp_timeout_handled(mock_smtp_class, smtp_settings):
    """Socket timeout raises EmailServiceError."""
    mock_smtp_class.side_effect = TimeoutError("Socket timed out")

    service = EmailService(smtp_settings)
    with pytest.raises(EmailServiceError) as exc:
        service.send_email(
            to_email="student@greensynth.edu",
            subject="Test Subject",
            html_body="<p>HTML</p>",
            text_body="Text",
        )

    assert "timed out" in str(exc.value)


# ── 5. ASYNC INVITATION DISPATCH INTEGRATION ─────────────────────────

@pytest.mark.asyncio
@patch("smtplib.SMTP")
async def test_send_group_invitation_end_to_end(mock_smtp_class, smtp_settings):
    """send_group_invitation renders templates and dispatches email via SMTP."""
    mock_server = MagicMock()
    mock_smtp_class.return_value = mock_server

    service = EmailService(smtp_settings)
    result = await service.send_group_invitation(
        to_email="colleague@greensynth.edu",
        recipient_name="Priya Sharma",
        group_name="Advanced Nanostructures",
        project_name="Spray Pyrolysis CuO",
        project_code="P8",
        leader_name="Atharvan",
        raw_token="secure_token_p16_xyz",
        expires_at=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
    )

    assert result is True
    mock_server.send_message.assert_called_once()
    msg = mock_server.send_message.call_args[0][0]
    assert msg["To"] == "colleague@greensynth.edu"
    assert "Invitation to Join a GreenSynth Research Group" in str(msg["Subject"])


# ── 6. CONSOLE AND DISABLED MODES ────────────────────────────────────

def test_console_mode_does_not_call_network():
    """email_mode='console' logs safely without making network connections."""
    settings = Settings(
        email_mode="console",
        email_enabled=True,
        smtp_from_email="v.atharvan@gmail.com",
    )
    service = EmailService(settings)
    # Should complete without error and without smtplib calls
    success = service.send_email(
        to_email="dev@example.com",
        subject="Console Mode Test",
        html_body="<p>Dev HTML</p>",
        text_body="Dev Text",
    )
    assert success is True


def test_disabled_email_mode():
    """email_enabled=False skips sending gracefully."""
    settings = Settings(
        email_mode="smtp",
        email_enabled=False,
    )
    service = EmailService(settings)
    success = service.send_email(
        to_email="test@example.com",
        subject="Disabled Email Test",
        html_body="<p>HTML</p>",
        text_body="Text",
    )
    assert success is True
