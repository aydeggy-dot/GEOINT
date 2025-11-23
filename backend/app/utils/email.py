"""
Email service using Brevo (formerly Sendinblue) or Gmail SMTP
Handles transactional emails for authentication and notifications
"""
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import List, Optional
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import Gmail service
try:
    from app.utils.email_gmail import GmailEmailService
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logger.warning("Gmail SMTP module not available")


class EmailService:
    """Email service wrapper for Brevo API"""

    def __init__(self):
        """Initialize Brevo API client"""
        if not settings.BREVO_API_KEY:
            logger.warning("BREVO_API_KEY not set. Email functionality will be disabled.")
            self.api_instance = None
            return

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def send_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send a transactional email via Brevo

        Args:
            to_email: Recipient email address
            to_name: Recipient name (optional)
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.api_instance:
            logger.error("Email service not initialized. Check BREVO_API_KEY.")
            return False

        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email, "name": to_name or to_email}],
                sender={
                    "email": settings.EMAIL_FROM_ADDRESS,
                    "name": settings.EMAIL_FROM_NAME
                },
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent successfully to {to_email}. Message ID: {response.message_id}")
            return True

        except ApiException as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False

    def send_verification_email(self, to_email: str, to_name: Optional[str], verification_link: str) -> bool:
        """
        Send email verification link

        Args:
            to_email: User's email address
            to_name: User's name
            verification_link: Complete verification URL with token

        Returns:
            bool: Success status
        """
        subject = "Verify your email - Nigeria Security EWS"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #008751; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #008751;
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Nigeria Security Early Warning System</h1>
                </div>
                <div class="content">
                    <h2>Welcome{f", {to_name}" if to_name else ""}!</h2>
                    <p>Thank you for registering with the Nigeria Security Early Warning System.</p>
                    <p>Please verify your email address by clicking the button below:</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #008751;">{verification_link}</p>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Nigeria Security Early Warning System &copy; 2025</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Nigeria Security Early Warning System!

        Please verify your email address by visiting this link:
        {verification_link}

        This link will expire in 24 hours.

        If you didn't create an account, please ignore this email.
        """

        return self.send_email(to_email, to_name, subject, html_content, text_content)

    def send_password_reset_email(self, to_email: str, to_name: Optional[str], reset_link: str) -> bool:
        """
        Send password reset link

        Args:
            to_email: User's email address
            to_name: User's name
            reset_link: Complete password reset URL with token

        Returns:
            bool: Success status
        """
        subject = "Reset your password - Nigeria Security EWS"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #008751; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #008751;
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .warning {{ color: #DC2626; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset the password for your account{f" ({to_name})" if to_name else ""}.</p>
                    <p>Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #008751;">{reset_link}</p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p class="warning">If you didn't request a password reset, please ignore this email and ensure your account is secure.</p>
                </div>
                <div class="footer">
                    <p>Nigeria Security Early Warning System &copy; 2025</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        We received a request to reset the password for your account.

        Click this link to reset your password:
        {reset_link}

        This link will expire in 1 hour.

        If you didn't request a password reset, please ignore this email.
        """

        return self.send_email(to_email, to_name, subject, html_content, text_content)

    def send_2fa_code_email(self, to_email: str, to_name: Optional[str], code: str) -> bool:
        """
        Send 2FA verification code via email

        Args:
            to_email: User's email address
            to_name: User's name
            code: 6-digit verification code

        Returns:
            bool: Success status
        """
        subject = "Your verification code - Nigeria Security EWS"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #008751; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .code {{ font-size: 32px; font-weight: bold; letter-spacing: 5px; text-align: center;
                        padding: 20px; background-color: #f0f0f0; border: 2px dashed #008751;
                        margin: 20px 0; color: #008751; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verification Code</h1>
                </div>
                <div class="content">
                    <h2>Two-Factor Authentication</h2>
                    <p>Your verification code is:</p>
                    <div class="code">{code}</div>
                    <p><strong>This code will expire in 10 minutes.</strong></p>
                    <p>Enter this code to complete your login.</p>
                    <p>If you didn't attempt to log in, please secure your account immediately.</p>
                </div>
                <div class="footer">
                    <p>Nigeria Security Early Warning System &copy; 2025</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Two-Factor Authentication Code

        Your verification code is: {code}

        This code will expire in 10 minutes.

        If you didn't attempt to log in, please secure your account.
        """

        return self.send_email(to_email, to_name, subject, html_content, text_content)

    def send_security_alert(self, to_email: str, to_name: Optional[str], event: str, details: str) -> bool:
        """
        Send security alert notification

        Args:
            to_email: User's email address
            to_name: User's name
            event: Security event (e.g., "New login from unknown device")
            details: Event details

        Returns:
            bool: Success status
        """
        subject = f"Security Alert - {event}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #DC2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .alert-box {{ background-color: #FEE2E2; border-left: 4px solid #DC2626; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Security Alert</h1>
                </div>
                <div class="content">
                    <h2>{event}</h2>
                    <div class="alert-box">
                        <p><strong>Details:</strong></p>
                        <p>{details}</p>
                    </div>
                    <p>If this was you, you can safely ignore this email.</p>
                    <p>If you didn't perform this action, please:</p>
                    <ul>
                        <li>Change your password immediately</li>
                        <li>Enable two-factor authentication if not already enabled</li>
                        <li>Review your account activity</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>Nigeria Security Early Warning System &copy; 2025</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Security Alert: {event}

        Details: {details}

        If this was you, you can safely ignore this email.

        If you didn't perform this action, please:
        - Change your password immediately
        - Enable two-factor authentication
        - Review your account activity
        """

        return self.send_email(to_email, to_name, subject, html_content, text_content)


# Singleton instance - use Gmail if configured, otherwise Brevo
if settings.USE_GMAIL and GMAIL_AVAILABLE:
    if settings.GMAIL_EMAIL and settings.GMAIL_APP_PASSWORD:
        logger.info("Using Gmail SMTP for email service")
        email_service = GmailEmailService(
            smtp_email=settings.GMAIL_EMAIL,
            smtp_password=settings.GMAIL_APP_PASSWORD,
            from_name=settings.EMAIL_FROM_NAME
        )
    else:
        logger.warning("USE_GMAIL is True but credentials not set. Email functionality disabled.")
        email_service = None
else:
    logger.info("Using Brevo API for email service")
    email_service = EmailService()
