"""
Upgrade User to Admin Script
Use this to grant admin access to users
"""
import psycopg2
import sys

def upgrade_to_admin(email: str, role_name: str = "super_admin"):
    """Upgrade a user to admin role"""
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
        cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            print(f"[ERROR] User with email '{email}' not found")
            cur.close()
            conn.close()
            return False

        user_id, user_email = user

        # Get the role ID
        cur.execute("SELECT id, name FROM roles WHERE name = %s", (role_name,))
        role = cur.fetchone()

        if not role:
            print(f"[ERROR] Role '{role_name}' not found")
            cur.close()
            conn.close()
            return False

        role_id, role_name_db = role

        # Check if user already has this role
        cur.execute(
            "SELECT 1 FROM user_roles WHERE user_id = %s AND role_id = %s",
            (user_id, role_id)
        )
        already_has_role = cur.fetchone()

        if already_has_role:
            print(f"[OK] User '{email}' already has '{role_name}' role")
            cur.close()
            conn.close()
            return True

        # Add the role to the user
        cur.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
            (user_id, role_id)
        )
        conn.commit()

        print(f"[SUCCESS] User '{email}' upgraded to '{role_name}'")
        print(f"   User ID: {user_id}")
        print(f"   Role ID: {role_id}")
        print(f"   The user now has full admin access!")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upgrade_to_admin.py <email> [role]")
        print("Example: python upgrade_to_admin.py user@example.com")
        print("Example: python upgrade_to_admin.py user@example.com admin")
        print("\nAvailable roles: super_admin, admin, analyst, field_officer, viewer")
        sys.exit(1)

    email = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "super_admin"
    upgrade_to_admin(email, role)
