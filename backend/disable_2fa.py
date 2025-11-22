"""
Disable 2FA for a user
"""
import psycopg2
import sys

def disable_2fa(email: str):
    """Disable 2FA for a user"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nigeria_security",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()

        # Get user ID
        cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            print(f"[ERROR] User with email '{email}' not found")
            cur.close()
            conn.close()
            return False

        user_id, user_email = user

        # Check if user has 2FA enabled
        cur.execute(
            "SELECT enabled FROM two_factor_auth WHERE user_id = %s",
            (user_id,)
        )
        twofa = cur.fetchone()

        if not twofa:
            print(f"[OK] User '{email}' does not have 2FA set up")
            cur.close()
            conn.close()
            return True

        enabled = twofa[0]

        if not enabled:
            print(f"[OK] 2FA is already disabled for '{email}'")
            cur.close()
            conn.close()
            return True

        # Disable 2FA
        cur.execute(
            "DELETE FROM two_factor_auth WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()

        print(f"[SUCCESS] 2FA disabled for user '{email}'")
        print(f"   User ID: {user_id}")
        print(f"   You can now log in without 2FA code")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python disable_2fa.py <email>")
        print("Example: python disable_2fa.py user@example.com")
        sys.exit(1)

    email = sys.argv[1]
    disable_2fa(email)
