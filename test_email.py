"""
Test email sending with Brevo
Run this script to verify your Brevo API key and email configuration
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.utils.email import email_service
from app.config import get_settings

settings = get_settings()

def test_email():
    """Test sending a verification email"""

    # Check if API key is configured
    if not settings.BREVO_API_KEY or settings.BREVO_API_KEY == "":
        print("ERROR: BREVO_API_KEY is not configured!")
        print("\nPlease set the BREVO_API_KEY environment variable:")
        print("  Windows: set BREVO_API_KEY=your-api-key-here")
        print("  Linux/Mac: export BREVO_API_KEY=your-api-key-here")
        return False

    print("Testing Brevo email service...")
    print(f"From: {settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>")

    # Prompt for recipient email
    to_email = input("\nEnter your email address to receive test email: ").strip()

    if not to_email or '@' not in to_email:
        print("ERROR: Invalid email address")
        return False

    print(f"\nSending test verification email to {to_email}...")

    # Send test email
    success = email_service.send_verification_email(
        to_email=to_email,
        to_name="Test User",
        verification_link="https://nigeria-security-ews-tiqle.ondigitalocean.app/verify-email?token=test-token-123"
    )

    if success:
        print("\n✓ Email sent successfully!")
        print(f"Check your inbox at {to_email}")
        print("\nIf you don't see it:")
        print("  1. Check your spam/junk folder")
        print("  2. Verify the sender email is verified in Brevo")
        print("  3. Check Brevo dashboard for delivery status")
        return True
    else:
        print("\n✗ Failed to send email")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. Sender email not verified in Brevo")
        print("  3. Daily sending limit exceeded (300 emails/day on free plan)")
        print("  4. Recipient email is blocked")
        print("\nCheck Brevo dashboard for more details:")
        print("https://app.brevo.com/")
        return False

if __name__ == "__main__":
    try:
        test_email()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
