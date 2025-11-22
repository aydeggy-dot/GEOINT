"""
Debug backup code verification
"""
import requests
import psycopg2
import pyotp

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "debugtest@example.com",
    "password": "DebugTest123!@#",
    "name": "Debug Test User"
}

print("="*60)
print("BACKUP CODE DEBUG TEST")
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

# Register and verify
print("[STEP 1] Register and verify user")
response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
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
cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (TEST_USER["email"],))
conn.commit()
cur.close()
conn.close()

# Login
print("[STEP 2] Login")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": TEST_USER["email"], "password": TEST_USER["password"]}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Login: {response.status_code}")

# Setup 2FA
print("\n[STEP 3] Setup 2FA")
response = requests.post(f"{BASE_URL}/2fa/setup", headers=headers)
data = response.json()
secret = data["secret"]
backup_codes = data["backup_codes"]
print(f"Setup: {response.status_code}")
print(f"Backup codes generated: {len(backup_codes)}")
print(f"First backup code: '{backup_codes[0]}'")
print(f"Backup code length: {len(backup_codes[0])}")
print(f"Has dash: {'-' in backup_codes[0]}")

# Enable 2FA
print("\n[STEP 4] Enable 2FA")
totp = pyotp.TOTP(secret)
code = totp.now()
response = requests.post(
    f"{BASE_URL}/2fa/enable",
    json={"code": code},
    headers=headers
)
print(f"Enable: {response.status_code}")

# Test backup code verification
print("\n[STEP 5] Test backup code verification")
backup_code = backup_codes[0]
print(f"Testing backup code: '{backup_code}'")
print(f"Payload: {{'code': '{backup_code}'}}")

response = requests.post(
    f"{BASE_URL}/2fa/verify",
    json={"code": backup_code},
    headers=headers
)

print(f"\nResponse Status: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"Response Body:")
print(response.text)

if response.status_code == 200:
    print("\n✅ SUCCESS!")
else:
    print("\n❌ FAILED!")
    try:
        error_data = response.json()
        print(f"Error detail: {error_data}")
    except:
        pass

cleanup()
