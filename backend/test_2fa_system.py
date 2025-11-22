"""
Test 2FA System
Comprehensive testing of TOTP two-factor authentication
"""
import requests
import psycopg2
import pyotp

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "2fatest@example.com",
    "password": "Test2FA123!@#",
    "name": "2FA Test User"
}

print("="*60)
print("2FA SYSTEM TEST")
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
        cur.execute("DELETE FROM users WHERE email = %s", (TEST_USER["email"],))
        conn.commit()
        cur.close()
        conn.close()
        print("[CLEANUP] Removed test user\n")
    except:
        print("[CLEANUP] No existing user\n")

cleanup()

# Step 1: Register and verify user
print("[STEP 1] Creating test user...")
print("-" * 60)
response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
if response.status_code in [200, 201]:
    print(f"[PASS] User registered: {TEST_USER['email']}")
else:
    print(f"[FAIL] Registration failed")
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
    cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (TEST_USER["email"],))
    conn.commit()
    cur.close()
    conn.close()
    print("[PASS] Email verified\n")
except Exception as e:
    print(f"[FAIL] Verification failed: {e}")
    exit(1)

# Step 2: Login
print("[STEP 2] Logging in...")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": TEST_USER["email"], "password": TEST_USER["password"]}
)
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"[PASS] Login successful")
    print(f"  Token: {token[:30]}...\n")
else:
    print(f"[FAIL] Login failed")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Test 1: Check 2FA status (should be disabled)
print("[TEST 1] Check initial 2FA status...")
print("-" * 60)
response = requests.get(f"{BASE_URL}/2fa/status", headers=headers)
if response.status_code == 200:
    data = response.json()
    if not data["enabled"]:
        print(f"[PASS] 2FA disabled initially")
        print(f"  Status: {data}\n")
    else:
        print(f"[FAIL] 2FA should be disabled")
        exit(1)
else:
    print(f"[FAIL] Status check failed")
    exit(1)

# Test 2: Setup 2FA
print("[TEST 2] Setup 2FA (generate secret and QR code)...")
print("-" * 60)
response = requests.post(f"{BASE_URL}/2fa/setup", headers=headers)
if response.status_code == 200:
    data = response.json()
    secret = data["secret"]
    backup_codes = data["backup_codes"]
    qr_code = data["qr_code"]

    print(f"[PASS] 2FA setup successful")
    print(f"  Secret: {secret}")
    print(f"  Backup codes: {len(backup_codes)} generated")
    print(f"  QR code: {len(qr_code)} bytes")
    print(f"  First backup code: {backup_codes[0]}\n")
else:
    print(f"[FAIL] Setup failed: {response.status_code}")
    print(response.json())
    exit(1)

# Test 3: Enable 2FA with valid code
print("[TEST 3] Enable 2FA with TOTP code...")
print("-" * 60)
# Generate valid TOTP code
totp = pyotp.TOTP(secret)
code = totp.now()
print(f"  Generated code: {code}")

response = requests.post(
    f"{BASE_URL}/2fa/enable",
    json={"code": code},
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"[PASS] 2FA enabled successfully")
    print(f"  Message: {data['message']}\n")
else:
    print(f"[FAIL] Enable failed: {response.status_code}")
    print(response.json())
    exit(1)

# Test 4: Verify 2FA status (should be enabled now)
print("[TEST 4] Check 2FA status after enabling...")
print("-" * 60)
response = requests.get(f"{BASE_URL}/2fa/status", headers=headers)
if response.status_code == 200:
    data = response.json()
    if data["enabled"] and data["method"] == "totp":
        print(f"[PASS] 2FA enabled successfully")
        print(f"  Method: {data['method']}")
        print(f"  Backup codes remaining: {data['backup_codes_remaining']}\n")
    else:
        print(f"[FAIL] 2FA should be enabled")
        exit(1)
else:
    print(f"[FAIL] Status check failed")

# Test 5: Verify TOTP code
print("[TEST 5] Verify TOTP code...")
print("-" * 60)
code = totp.now()
response = requests.post(
    f"{BASE_URL}/2fa/verify",
    json={"code": code},
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"[PASS] TOTP code verified")
    print(f"  Message: {data['message']}\n")
else:
    print(f"[FAIL] Verification failed")
    exit(1)

# Test 6: Verify backup code
print("[TEST 6] Verify backup code...")
print("-" * 60)
backup_code = backup_codes[0]
response = requests.post(
    f"{BASE_URL}/2fa/verify",
    json={"code": backup_code},
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"[PASS] Backup code verified")
    print(f"  Message: {data['message']}")
    print(f"  Backup codes remaining: {data['backup_codes_remaining']}\n")
else:
    print(f"[FAIL] Backup code verification failed")
    exit(1)

# Test 7: Regenerate backup codes
print("[TEST 7] Regenerate backup codes...")
print("-" * 60)
response = requests.post(f"{BASE_URL}/2fa/regenerate-codes", headers=headers)
if response.status_code == 200:
    data = response.json()
    new_backup_codes = data["backup_codes"]
    print(f"[PASS] Backup codes regenerated")
    print(f"  New codes: {len(new_backup_codes)} generated")
    print(f"  First new code: {new_backup_codes[0]}\n")
else:
    print(f"[FAIL] Regeneration failed")
    exit(1)

# Test 8: Disable 2FA with password
print("[TEST 8] Disable 2FA...")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/2fa/disable",
    json={"password": TEST_USER["password"]},
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"[PASS] 2FA disabled")
    print(f"  Message: {data['message']}\n")
else:
    print(f"[FAIL] Disable failed")
    exit(1)

# Test 9: Verify 2FA disabled
print("[TEST 9] Confirm 2FA is disabled...")
print("-" * 60)
response = requests.get(f"{BASE_URL}/2fa/status", headers=headers)
if response.status_code == 200:
    data = response.json()
    if not data["enabled"]:
        print(f"[PASS] 2FA confirmed disabled\n")
    else:
        print(f"[FAIL] 2FA should be disabled")
        exit(1)
else:
    print(f"[FAIL] Status check failed")

# Cleanup
cleanup()

print("="*60)
print("[PASS][PASS][PASS] ALL 2FA TESTS PASSED! [PASS][PASS][PASS]")
print("="*60)
print("\n2FA System Summary:")
print("  - Setup & enable working")
print("  - TOTP code verification working")
print("  - Backup code verification working")
print("  - Backup code regeneration working")
print("  - Disable functionality working")
print("  - QR code generation working")
print("\n" + "="*60)
