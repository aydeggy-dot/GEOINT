"""
Test RBAC System - Verify Roles and Permissions
Test that roles and permissions are properly configured and accessible via API
"""
import requests
import psycopg2

BASE_URL = "http://localhost:8000/api/v1"
TEST_USERS = {
    "admin": {
        "email": "admin@example.com",
        "password": "Admin123!@#",
        "name": "Admin User",
        "role": "admin"
    },
    "moderator": {
        "email": "moderator@example.com",
        "password": "Moderator123!@#",
        "name": "Moderator User",
        "role": "moderator"
    },
    "analyst": {
        "email": "analyst@example.com",
        "password": "Analyst123!@#",
        "name": "Analyst User",
        "role": "analyst"
    }
}

print("="*60)
print("RBAC SYSTEM VERIFICATION TEST")
print("="*60)

# Clean up test users
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="nigeria_security",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    for user_data in TEST_USERS.values():
        cur.execute("DELETE FROM users WHERE email = %s", (user_data["email"],))
    conn.commit()
    cur.close()
    conn.close()
    print("[CLEANUP] Removed existing test users\n")
except Exception as e:
    print(f"[CLEANUP] No existing users to remove\n")

# Test 1: Verify roles exist in database
print("[TEST 1] Verifying roles in database...")
print("-" * 60)
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="nigeria_security",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    cur.execute("SELECT name, display_name FROM roles ORDER BY name")
    roles = cur.fetchall()

    expected_roles = ['admin', 'analyst', 'moderator', 'super_admin', 'user', 'verified_reporter']
    found_roles = [role[0] for role in roles]

    if set(expected_roles) == set(found_roles):
        print("[PASS] All 6 expected roles found:")
        for role_name, display_name in roles:
            print(f"  - {role_name}: {display_name}")
    else:
        print(f"[FAIL] Role mismatch. Expected: {expected_roles}, Found: {found_roles}")
        exit(1)

    cur.close()
    conn.close()
except Exception as e:
    print(f"[FAIL] Database query error: {e}")
    exit(1)

# Test 2: Verify permissions exist
print("\n[TEST 2] Verifying permissions in database...")
print("-" * 60)
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="nigeria_security",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM permissions")
    perm_count = cur.fetchone()[0]

    if perm_count == 29:
        print(f"[PASS] All 29 permissions created")

        cur.execute("SELECT resource, COUNT(*) FROM permissions GROUP BY resource ORDER BY resource")
        resource_counts = cur.fetchall()
        print("\n  Permissions by resource:")
        for resource, count in resource_counts:
            print(f"    {resource}: {count} permissions")
    else:
        print(f"[FAIL] Expected 29 permissions, found {perm_count}")
        exit(1)

    cur.close()
    conn.close()
except Exception as e:
    print(f"[FAIL] Database query error: {e}")
    exit(1)

# Test 3: Verify role-permission associations
print("\n[TEST 3] Verifying role-permission associations...")
print("-" * 60)
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="nigeria_security",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT r.name, COUNT(rp.permission_id)
        FROM roles r
        LEFT JOIN role_permissions rp ON r.id = rp.role_id
        GROUP BY r.name
        ORDER BY r.name
    """)
    role_perms = cur.fetchall()

    expected_counts = {
        'admin': 27,
        'analyst': 15,
        'moderator': 12,
        'super_admin': 29,
        'user': 2,
        'verified_reporter': 5
    }

    all_correct = True
    for role_name, count in role_perms:
        expected = expected_counts.get(role_name, 0)
        if count == expected:
            print(f"  [PASS] {role_name}: {count} permissions")
        else:
            print(f"  [FAIL] {role_name}: Expected {expected}, got {count}")
            all_correct = False

    if not all_correct:
        exit(1)

    cur.close()
    conn.close()
except Exception as e:
    print(f"[FAIL] Database query error: {e}")
    exit(1)

# Test 4: Register test users and assign roles
print("\n[TEST 4] Creating test users with different roles...")
print("-" * 60)

for role_key, user_data in TEST_USERS.items():
    # Register user
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code not in [200, 201]:
        print(f"[FAIL] Failed to register {role_key}: {response.status_code}")
        exit(1)

    # Verify email in database
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nigeria_security",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()

        # Verify email
        cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (user_data["email"],))

        # Get user ID
        cur.execute("SELECT id FROM users WHERE email = %s", (user_data["email"],))
        user_id = cur.fetchone()[0]

        # Get role ID
        cur.execute("SELECT id FROM roles WHERE name = %s", (user_data["role"],))
        role_id = cur.fetchone()[0]

        # Assign role
        cur.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, role_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        print(f"  [PASS] Created {role_key} user with {user_data['role']} role")
    except Exception as e:
        print(f"  [FAIL] Failed to assign role to {role_key}: {e}")
        exit(1)

# Test 5: Login and verify users have roles
print("\n[TEST 5] Verifying users can login and have correct roles...")
print("-" * 60)

for role_key, user_data in TEST_USERS.items():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )

    if response.status_code == 200:
        data = response.json()
        user = data.get("user", {})
        roles = user.get("roles", [])

        if user_data["role"] in roles:
            print(f"  [PASS] {role_key} logged in with role: {user_data['role']}")
        else:
            print(f"  [FAIL] {role_key} missing expected role. Got: {roles}")
            exit(1)
    else:
        print(f"  [FAIL] {role_key} login failed: {response.status_code}")
        exit(1)

# Cleanup
print("\n[CLEANUP] Removing test users...")
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="nigeria_security",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    for user_data in TEST_USERS.values():
        cur.execute("DELETE FROM users WHERE email = %s", (user_data["email"],))
    conn.commit()
    cur.close()
    conn.close()
    print("[PASS] Test users removed\n")
except Exception as e:
    print(f"[FAIL] Cleanup failed: {e}\n")

print("="*60)
print("[PASS][PASS][PASS] ALL RBAC TESTS PASSED! [PASS][PASS][PASS]")
print("="*60)
print("\nRBAC System Summary:")
print("  - 6 roles created (user, verified_reporter, moderator, analyst, admin, super_admin)")
print("  - 29 permissions across 6 resources")
print("  - Role assignments working correctly")
print("  - Users can login with assigned roles")
print("\n" + "="*60)
