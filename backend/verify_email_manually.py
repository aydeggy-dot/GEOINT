"""
Manual Email Verification Script
Use this to verify user emails when email service is not configured
"""
import psycopg2
import sys

def verify_email(email: str):
    """Manually verify a user's email in the database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nigeria_security",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()

        # Check if user exists
        cur.execute("SELECT id, email, email_verified FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            print(f"[ERROR] User with email '{email}' not found")
            cur.close()
            conn.close()
            return False

        user_id, user_email, already_verified = user

        if already_verified:
            print(f"[OK] Email '{email}' is already verified")
            cur.close()
            conn.close()
            return True

        # Verify the email
        cur.execute(
            "UPDATE users SET email_verified = TRUE, status = 'active' WHERE email = %s",
            (email,)
        )
        conn.commit()

        print(f"[SUCCESS] Successfully verified email: {email}")
        print(f"   User ID: {user_id}")
        print(f"   You can now log in!")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_email_manually.py <email>")
        print("Example: python verify_email_manually.py user@example.com")
        sys.exit(1)

    email = sys.argv[1]
    verify_email(email)
