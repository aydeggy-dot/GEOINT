"""
Test Token Refresh Functionality - Verify Timezone Fix
"""
import requests
import psycopg2

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "refreshtest@example.com",
    "password": "RefreshTest123!@#",
    "name": "Refresh Test User"
}

print("="*60)
print("TOKEN REFRESH TEST - Timezone Fix Verification")
print("="*60)

# Clean up any existing test user
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
    print("[CLEANUP] Removed existing test user\n")
except Exception as e:
    print(f"[CLEANUP] No existing user to remove\n")

# Step 1: Register
print("[STEP 1] Registering user...")
response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
if response.status_code in [200, 201]:
    print(f"[PASS] Registration successful: {response.json()['email']}\n")
else:
    print(f"[FAIL] Registration failed: {response.status_code}")
    print(response.json())
    exit(1)

# Step 2: Verify email manually in database
print("[STEP 2] Verifying email in database...")
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="nigeria_security",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET email_verified = TRUE WHERE email = %s",
        (TEST_USER["email"],)
    )
    conn.commit()
    cur.close()
    conn.close()
    print("[PASS] Email verified\n")
except Exception as e:
    print(f"[FAIL] Verification failed: {e}")
    exit(1)

# Step 3: Login to get tokens
print("[STEP 3] Logging in to get tokens...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
)
if response.status_code == 200:
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    print(f"[PASS] Login successful")
    print(f"  Access Token: {access_token[:30]}...")
    print(f"  Refresh Token: {refresh_token[:30]}...\n")
else:
    print(f"[FAIL] Login failed: {response.status_code}")
    print(response.json())
    exit(1)

# Step 4: TEST TOKEN REFRESH (The critical test!)
print("[STEP 4] Testing token refresh...")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": refresh_token}
)

if response.status_code == 200:
    data = response.json()
    new_access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]

    print("[PASS][PASS][PASS] TOKEN REFRESH SUCCESSFUL! [PASS][PASS][PASS]")
    print(f"\n  Old Access Token: {access_token[:30]}...")
    print(f"  New Access Token: {new_access_token[:30]}...")
    print(f"\n  Old Refresh Token: {refresh_token[:30]}...")
    print(f"  New Refresh Token: {new_refresh_token[:30]}...")
    print(f"\n  Token Type: {data['token_type']}")
    print(f"  Expires In: {data['expires_in']} seconds")
    print("\n" + "="*60)
    print("[PASS] TIMEZONE FIX VERIFIED - Token refresh working!")
    print("="*60 + "\n")

    # Verify new token works
    print("[STEP 5] Verifying new access token works...")
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    if response.status_code == 200:
        user = response.json()
        print(f"[PASS] New token works - User: {user['name']} ({user['email']})")
        print("\n[PASS][PASS][PASS] ALL TESTS PASSED! [PASS][PASS][PASS]\n")
    else:
        print(f"[FAIL] New token validation failed: {response.status_code}")

else:
    print(f"[FAIL][FAIL][FAIL] TOKEN REFRESH FAILED! [FAIL][FAIL][FAIL]")
    print(f"\n  Status Code: {response.status_code}")
    try:
        error = response.json()
        print(f"  Error: {error}")
    except:
        print(f"  Response: {response.text}")
    print("\n" + "="*60)
    print("[FAIL] TIMEZONE FIX NOT WORKING - Check server logs")
    print("="*60 + "\n")
    exit(1)

# Cleanup
print("[CLEANUP] Removing test user...")
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
    print("[PASS] Test user removed\n")
except Exception as e:
    print(f"[FAIL] Cleanup failed: {e}\n")
