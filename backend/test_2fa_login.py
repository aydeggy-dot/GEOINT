"""
Test 2FA Integration in Login Flow
Comprehensive testing of 2FA during authentication
"""
import requests
import psycopg2
import pyotp

BASE_URL = "http://localhost:8000/api/v1"

# Test users
USER_NO_2FA = {
    "email": "user_no2fa@example.com",
    "password": "TestNoFA123!@#",
    "name": "User Without 2FA"
}

USER_WITH_2FA = {
    "email": "user_with2fa@example.com",
    "password": "TestWith2FA123!@#",
    "name": "User With 2FA"
}

print("="*60)
print("2FA LOGIN INTEGRATION TEST")
print("="*60)

# Cleanup
def cleanup():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nigeria_security",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email IN (%s, %s)",
                   (USER_NO_2FA["email"], USER_WITH_2FA["email"]))
        conn.commit()
        cur.close()
        conn.close()
        print("[CLEANUP] Removed test users\n")
    except:
        print("[CLEANUP] No existing users\n")

cleanup()

# =================================================================
# TEST 1: Login without 2FA (normal flow)
# =================================================================
print("[TEST 1] Login without 2FA enabled")
print("-" * 60)

# Register user
response = requests.post(f"{BASE_URL}/auth/register", json=USER_NO_2FA)
print(f"Registration: {response.status_code}")

# Verify email
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="nigeria_security",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()
cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (USER_NO_2FA["email"],))
conn.commit()

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_NO_2FA["email"],
        "password": USER_NO_2FA["password"]
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"[PASS] Login successful without 2FA")
    print(f"  Access token received: {data['access_token'][:30]}...")
    print(f"  User: {data['user']['email']}\n")
else:
    print(f"[FAIL] Login failed: {response.status_code}")
    print(f"  {response.json()}\n")
    exit(1)

# =================================================================
# TEST 2: Login with 2FA enabled but no code provided
# =================================================================
print("[TEST 2] Login with 2FA enabled but no code provided")
print("-" * 60)

# Register second user
response = requests.post(f"{BASE_URL}/auth/register", json=USER_WITH_2FA)
print(f"Registration: {response.status_code}")

# Verify email
cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (USER_WITH_2FA["email"],))
conn.commit()

# Login to get token for 2FA setup
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_WITH_2FA["email"],
        "password": USER_WITH_2FA["password"]
    }
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Setup 2FA
response = requests.post(f"{BASE_URL}/2fa/setup", headers=headers)
data = response.json()
secret = data["secret"]
backup_codes = data["backup_codes"]
print(f"2FA setup: Secret = {secret}")

# Enable 2FA
totp = pyotp.TOTP(secret)
code = totp.now()
response = requests.post(
    f"{BASE_URL}/2fa/enable",
    json={"code": code},
    headers=headers
)
print(f"2FA enabled: {response.status_code}")

# Try to login WITHOUT 2FA code
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_WITH_2FA["email"],
        "password": USER_WITH_2FA["password"]
        # No two_factor_code provided
    }
)

if response.status_code == 403:
    data = response.json()
    if "Two-factor authentication" in data["detail"]:
        print(f"[PASS] Login correctly rejected without 2FA code")
        print(f"  Status: {response.status_code}")
        print(f"  Message: {data['detail']}")
        print(f"  Headers: {dict(response.headers).get('X-Requires-2FA', 'Not present')}\n")
    else:
        print(f"[FAIL] Wrong error message: {data['detail']}\n")
        exit(1)
else:
    print(f"[FAIL] Should have rejected login without 2FA code")
    print(f"  Status: {response.status_code}\n")
    exit(1)

# =================================================================
# TEST 3: Login with 2FA enabled and valid TOTP code
# =================================================================
print("[TEST 3] Login with 2FA enabled and valid TOTP code")
print("-" * 60)

# Generate fresh TOTP code
code = totp.now()
print(f"Generated TOTP code: {code}")

# Login WITH valid 2FA code
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_WITH_2FA["email"],
        "password": USER_WITH_2FA["password"],
        "two_factor_code": code
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"[PASS] Login successful with valid TOTP code")
    print(f"  Access token received: {data['access_token'][:30]}...")
    print(f"  User: {data['user']['email']}\n")
else:
    print(f"[FAIL] Login failed with valid TOTP code")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}\n")
    exit(1)

# =================================================================
# TEST 4: Login with 2FA enabled and valid backup code
# =================================================================
print("[TEST 4] Login with 2FA enabled and valid backup code")
print("-" * 60)

backup_code = backup_codes[0]
print(f"Using backup code: {backup_code}")

# Login WITH valid backup code
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_WITH_2FA["email"],
        "password": USER_WITH_2FA["password"],
        "two_factor_code": backup_code
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"[PASS] Login successful with valid backup code")
    print(f"  Access token received: {data['access_token'][:30]}...")
    print(f"  User: {data['user']['email']}")
    print(f"  Backup code consumed (will not work again)\n")
else:
    print(f"[FAIL] Login failed with valid backup code")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}\n")
    exit(1)

# =================================================================
# TEST 5: Verify used backup code cannot be reused
# =================================================================
print("[TEST 5] Verify used backup code cannot be reused")
print("-" * 60)

# Try to use the same backup code again
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_WITH_2FA["email"],
        "password": USER_WITH_2FA["password"],
        "two_factor_code": backup_code  # Same code as before
    }
)

if response.status_code == 401:
    print(f"[PASS] Login correctly rejected with used backup code")
    print(f"  Status: {response.status_code}")
    print(f"  Message: {response.json()['detail']}\n")
else:
    print(f"[FAIL] Should have rejected used backup code")
    print(f"  Status: {response.status_code}\n")
    exit(1)

# =================================================================
# TEST 6: Login with invalid 2FA code
# =================================================================
print("[TEST 6] Login with invalid 2FA code")
print("-" * 60)

# Try to login with invalid code
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USER_WITH_2FA["email"],
        "password": USER_WITH_2FA["password"],
        "two_factor_code": "000000"  # Invalid code
    }
)

if response.status_code == 401:
    data = response.json()
    print(f"[PASS] Login correctly rejected with invalid 2FA code")
    print(f"  Status: {response.status_code}")
    print(f"  Message: {data['detail']}\n")
else:
    print(f"[FAIL] Should have rejected invalid 2FA code")
    print(f"  Status: {response.status_code}\n")
    exit(1)

# Cleanup
cur.close()
conn.close()
cleanup()

print("="*60)
print("[PASS][PASS][PASS] ALL 2FA LOGIN TESTS PASSED! [PASS][PASS][PASS]")
print("="*60)
print("\n2FA Login Integration Summary:")
print("  - Login without 2FA works normally")
print("  - Login with 2FA requires code")
print("  - TOTP code verification works")
print("  - Backup code verification works")
print("  - Used backup codes are rejected")
print("  - Invalid codes are rejected")
print("\n" + "="*60)
