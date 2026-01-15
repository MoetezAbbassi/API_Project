"""
Email Service - Handle sending verification codes and notifications
"""

import smtplib
import random
import string
import logging
import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # App password for Gmail
SENDER_EMAIL = os.getenv('SENDER_EMAIL', SMTP_USERNAME)
SENDER_NAME = os.getenv('SENDER_NAME', 'Fitness Tracker')

# For development/testing - mock email sending
EMAIL_MOCK_MODE = os.getenv('EMAIL_MOCK_MODE', 'true').lower() == 'true'
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', '').lower()

# MailSender provider settings (placeholders - fill in your values in .env)
MAILSENDER_API_URL = os.getenv('MAILSENDER_API_URL', '')
MAILSENDER_API_KEY = os.getenv('MAILSENDER_API_KEY', '')
MAILSENDER_SENDER_EMAIL = os.getenv('MAILSENDER_SENDER_EMAIL', SENDER_EMAIL)
MAILSENDER_SENDER_NAME = os.getenv('MAILSENDER_SENDER_NAME', SENDER_NAME)


def generate_verification_code(length: int = 6) -> str:
    """
    Generate a random numeric verification code
    
    Args:
        length: Length of the code (default 6)
        
    Returns:
        String of random digits
    """
    return ''.join(random.choices(string.digits, k=length))


def send_via_mailsender(to_email: str, subject: str, html_body: str, text_body: str = None, from_email: str = None, from_name: str = None) -> Tuple[bool, str]:
    """
    Send email via MailSender HTTP API.

    Returns (success, message)
    """
    if not MAILSENDER_API_URL or not MAILSENDER_API_KEY:
        logger.error('MailSender configuration missing')
        return False, 'MailSender not configured'

    # Some providers (e.g. MailerSend) expect a slightly different payload/endpoint.
    api_url = MAILSENDER_API_URL or ''
    # If user set base URL like https://api.mailersend.com/v1/ append the email path
    if 'mailersend.com' in api_url and not api_url.rstrip('/').endswith('/email'):
        api_url = api_url.rstrip('/') + '/email'

    # choose from address (explicit override > MAILSENDER_SENDER_EMAIL > fallback SENDER_EMAIL)
    use_from_email = from_email or MAILSENDER_SENDER_EMAIL or SENDER_EMAIL
    use_from_name = from_name or MAILSENDER_SENDER_NAME or SENDER_NAME

    # Default generic payload (some providers support this)
    payload = {
        "from": {"email": use_from_email, "name": use_from_name},
        "to": [{"email": to_email}],
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body or ''},
            {"type": "text/html", "value": html_body}
        ]
    }

    # If targeting MailerSend, adjust payload shape
    if 'mailersend.com' in api_url:
        payload = {
            "from": {"email": use_from_email, "name": use_from_name},
            "to": [{"email": to_email}],
            "subject": subject,
            "html": html_body,
            "text": text_body or ''
        }

    headers = {
        "Authorization": f"Bearer {MAILSENDER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(api_url or MAILSENDER_API_URL, json=payload, headers=headers, timeout=10)
        if 200 <= resp.status_code < 300:
            return True, 'sent'
        else:
            logger.error('MailSender returned HTTP %s: %s', resp.status_code, resp.text)
            return False, f'MailSender error: {resp.status_code} {resp.text}'
    except Exception as e:
        logger.exception('MailSender exception: %s', e)
        return False, f'Exception: {str(e)}'


def send_verification_email(to_email: str, code: str, username: str) -> Tuple[bool, str]:
    """
    Send verification code email to user
    
    Args:
        to_email: Recipient email address
        code: Verification code to send
        username: Username for personalization
        
    Returns:
        Tuple of (success, message)
    """
    if EMAIL_MOCK_MODE:
        # In mock mode, just log the code (for development)
        import sys
        code_display = f"""
╔══════════════════════════════════════════════════════════╗
║           ✉️  VERIFICATION CODE (MOCK MODE)             ║
╚══════════════════════════════════════════════════════════╝
  To: {to_email}
  Username: {username}
  Code: {code}
╔══════════════════════════════════════════════════════════╗
"""
        # Print to both stdout and stderr to ensure visibility
        print(code_display, file=sys.stdout)
        print(code_display, file=sys.stderr)
        logger.info(f"📧 [MOCK EMAIL] Verification code for {username} ({to_email}): {code}")
        return True, "Verification code sent (mock mode)"

    # Build plain/text and html content (used by providers)
    text_content = f"""
Hello {username},

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Fitness Tracker Team
        """

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #3182ce 0%, #ed8936 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: #1a202c; color: #3182ce; font-size: 32px; font-weight: bold; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 10px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏋️ Fitness Tracker</h1>
            <p>Login Verification</p>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            <p>Your verification code is:</p>
            <div class="code-box">{code}</div>
            <p>⏱️ This code will expire in <strong>10 minutes</strong>.</p>
            <p>If you didn't request this code, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2026 Fitness Tracker. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

    # If a provider other than SMTP is configured, use it
    mail_error_msg = None
    if EMAIL_PROVIDER == 'mailsender':
        try:
            success, msg = send_via_mailsender(to_email, f'Your Fitness Tracker Verification Code: {code}', html_content, text_content)
            if success:
                logger.info(f"Verification email sent to {to_email} via MailSender")
                return True, "Verification code sent successfully"
            else:
                mail_error_msg = msg or ''
                logger.error(f"MailSender failed: {msg}")
                logger.info("Attempting fallback: retry MailSender with SMTP username as From, then SMTP send")
                # If domain verification error, try resend using SMTP username as from address
                if 'domain must be verified' in (msg or '').lower() or 'ms42207' in (msg or '').lower():
                    alt_from = SMTP_USERNAME or MAILSENDER_SENDER_EMAIL or SENDER_EMAIL
                    try:
                        success2, msg2 = send_via_mailsender(to_email, f'Your Fitness Tracker Verification Code: {code}', html_content, text_content, from_email=alt_from, from_name=SENDER_NAME)
                        if success2:
                            logger.info(f"Verification email sent to {to_email} via MailSender using alt from {alt_from}")
                            return True, "Verification code sent successfully"
                        else:
                            mail_error_msg = msg2 or mail_error_msg
                            logger.error(f"MailSender retry with alt from failed: {msg2}")
                    except Exception as e:
                        logger.exception('MailSender retry exception: %s', e)
        except Exception as e:
            logger.exception('MailSender exception: %s', e)
            mail_error_msg = str(e)
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Using mock mode.")
        print(f"\n⚠️ Email not configured. Verification code: {code}\n")
        return True, f"Email not configured. Code: {code}"
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Your Fitness Tracker Verification Code: {code}'
        # Choose From address: if MailSender reported domain verification problems, use SMTP username as from
        from_addr = SENDER_EMAIL
        if mail_error_msg and ('domain must be verified' in mail_error_msg.lower() or 'ms42207' in mail_error_msg.lower()):
            from_addr = SMTP_USERNAME or SENDER_EMAIL
        msg['From'] = f'{SENDER_NAME} <{from_addr}>'
        msg['To'] = to_email
        
        # Plain text version
        text_content = f"""
Hello {username},

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Fitness Tracker Team
        """
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #3182ce 0%, #ed8936 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: #1a202c; color: #3182ce; font-size: 32px; font-weight: bold; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 10px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏋️ Fitness Tracker</h1>
            <p>Login Verification</p>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            <p>Your verification code is:</p>
            <div class="code-box">{code}</div>
            <p>⏱️ This code will expire in <strong>10 minutes</strong>.</p>
            <p>If you didn't request this code, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2026 Fitness Tracker. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email via SMTP. Use from_addr as envelope from to avoid MailerSend domain errors
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(from_addr, to_email, msg.as_string())
        
        logger.info(f"Verification email sent to {to_email}")
        return True, "Verification code sent successfully"
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        return False, "Email service authentication failed"
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
    except Exception as e:
        logger.error(f"Email error: {str(e)}")
        return False, f"Email service error: {str(e)}"


def create_verification_entry(user_id: str, code: str) -> dict:
    """
    Create a verification code entry in the database
    
    Args:
        user_id: User ID
        code: Generated verification code
        
    Returns:
        Dictionary with code entry details
    """
    from app.extensions import db
    from app.models import EmailVerificationCode
    
    # Invalidate any existing codes for this user
    existing_codes = db.session.query(EmailVerificationCode).filter_by(
        user_id=user_id,
        used=False
    ).all()
    
    for existing in existing_codes:
        existing.used = True
    
    # Create new verification code
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    verification = EmailVerificationCode(
        user_id=user_id,
        code=code,
        expires_at=expires_at,
        used=False
    )
    
    db.session.add(verification)
    db.session.commit()
    
    return {
        "code_id": verification.code_id,
        "expires_at": expires_at.isoformat(),
        "expires_in_seconds": 600
    }


def verify_code(user_id: str, code: str) -> Tuple[bool, str]:
    """
    Verify a verification code
    
    Args:
        user_id: User ID
        code: Code to verify
        
    Returns:
        Tuple of (is_valid, message)
    """
    from app.extensions import db
    from app.models import EmailVerificationCode
    
    verification = db.session.query(EmailVerificationCode).filter_by(
        user_id=user_id,
        code=code,
        used=False
    ).first()
    
    if not verification:
        return False, "Invalid verification code"
    
    if not verification.is_valid():
        return False, "Verification code has expired"
    
    # Mark code as used
    verification.used = True
    db.session.commit()
    
    return True, "Code verified successfully"
