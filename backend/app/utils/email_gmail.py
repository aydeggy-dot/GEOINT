"""
Gmail SMTP Email Service
Quick alternative to Brevo for development/testing
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GmailEmailService:
    """Email service using Gmail SMTP"""

    def __init__(
        self,
        smtp_email: str,
        smtp_password: str,  # Use App Password, not regular password
        from_name: str = "Nigeria Security EWS"
    ):
        self.smtp_email = smtp_email
        self.smtp_password = smtp_password
        self.from_name = from_name
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email via Gmail SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.smtp_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(
        self,
        to_email: str,
        to_name: str,
        verification_link: str
    ) -> bool:
        """Send email verification link"""
        subject = "Verify Your Email - Nigeria Security EWS"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Welcome to Nigeria Security Early Warning System</h2>
                <p>Hi {to_name},</p>
                <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}"
                       style="background-color: #2563eb; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_link}</p>
                <p>This link will expire in 24 hours.</p>
                <hr style="border: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't create this account, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Nigeria Security Early Warning System

        Hi {to_name},

        Thank you for registering. Please verify your email address by visiting:
        {verification_link}

        This link will expire in 24 hours.

        If you didn't create this account, please ignore this email.
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_link: str
    ) -> bool:
        """Send password reset link"""
        subject = "Password Reset Request - Nigeria Security EWS"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Password Reset Request</h2>
                <p>Hi {to_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background-color: #dc2626; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_link}</p>
                <p>This link will expire in 1 hour.</p>
                <hr style="border: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    If you didn't request this, please ignore this email. Your password won't change.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        Hi {to_name},

        We received a request to reset your password. Visit this link to create a new password:
        {reset_link}

        This link will expire in 1 hour.

        If you didn't request this, please ignore this email.
        """

        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance (will be initialized in config)
email_service: Optional[GmailEmailService] = None
