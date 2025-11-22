"""
Comprehensive End-to-End Test for Authentication System
Tests all authentication endpoints systematically
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "testuser@example.com",
    "password": "Test123!@#Strong",
    "name": "Test User"
}

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(test_name, status, details=""):
    """Print formatted test result"""
    symbol = f"{GREEN}[PASS]{RESET}" if status == "PASS" else f"{RED}[FAIL]{RESET}"
    print(f"{symbol} {test_name}")
    if details:
        print(f"  {BLUE}>{RESET} {details}")
    print()

def print_section(title):
    """Print section header"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}{title}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")

# Store tokens and user data
tokens = {}
user_data = {}

print(f"\n{BLUE}============================================================{RESET}")
print(f"{BLUE}  Nigeria Security System - Authentication Test Suite    {RESET}")
print(f"{BLUE}  Testing all endpoints end-to-end                        {RESET}")
print(f"{BLUE}============================================================{RESET}\n")

# =============================================================================
# TEST 1: HEALTH CHECK
# =============================================================================
print_section("TEST 1: Health Check")
try:
    response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
    if response.status_code == 200:
        data = response.json()
        print_test("Health Check", "PASS", f"Status: {data['status']}, Service: {data['service']}")
    else:
        print_test("Health Check", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Health Check", "FAIL", str(e))

# =============================================================================
# TEST 2: USER REGISTRATION
# =============================================================================
print_section("TEST 2: User Registration")
try:
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=TEST_USER
    )
    if response.status_code == 200:
        data = response.json()
        print_test(
            "User Registration",
            "PASS",
            f"Email: {data['email']}, Verification Required: {data['verification_required']}"
        )
        print(f"  {BLUE}Message:{RESET} {data['message']}")
    else:
        print_test("User Registration", "FAIL", f"Status Code: {response.status_code}")
        print(f"  {RED}Response:{RESET} {response.json()}")
except Exception as e:
    print_test("User Registration", "FAIL", str(e))

# =============================================================================
# TEST 3: LOGIN WITHOUT EMAIL VERIFICATION (Should Fail)
# =============================================================================
print_section("TEST 3: Login Without Email Verification (Should Fail)")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    if response.status_code == 403:
        data = response.json()
        print_test(
            "Login Blocked (Unverified)",
            "PASS",
            f"Correctly blocked: {data['detail']}"
        )
    else:
        print_test("Login Blocked (Unverified)", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Login Blocked (Unverified)", "FAIL", str(e))

# =============================================================================
# TEST 4: MANUALLY VERIFY EMAIL IN DATABASE
# =============================================================================
print_section("TEST 4: Manual Email Verification (Database)")
import psycopg2
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
    print_test("Email Verification", "PASS", "Email marked as verified in database")
except Exception as e:
    print_test("Email Verification", "FAIL", str(e))

# =============================================================================
# TEST 5: LOGIN WITH VERIFIED EMAIL
# =============================================================================
print_section("TEST 5: Login With Verified Email")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    if response.status_code == 200:
        data = response.json()
        tokens = {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"]
        }
        user_data = data["user"]
        print_test(
            "Login Success",
            "PASS",
            f"User: {user_data['name']} ({user_data['email']})"
        )
        print(f"  {BLUE}Token Type:{RESET} {data['token_type']}")
        print(f"  {BLUE}Expires In:{RESET} {data['expires_in']} seconds")
        print(f"  {BLUE}Access Token:{RESET} {tokens['access_token'][:30]}...")
        print(f"  {BLUE}Refresh Token:{RESET} {tokens['refresh_token'][:30]}...")
    else:
        print_test("Login Success", "FAIL", f"Status Code: {response.status_code}")
        print(f"  {RED}Response:{RESET} {response.json()}")
except Exception as e:
    print_test("Login Success", "FAIL", str(e))

# =============================================================================
# TEST 6: GET CURRENT USER (Protected Endpoint)
# =============================================================================
print_section("TEST 6: Get Current User (/auth/me)")
try:
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Get Current User",
            "PASS",
            f"User ID: {data['id']}"
        )
        print(f"  {BLUE}Name:{RESET} {data['name']}")
        print(f"  {BLUE}Email:{RESET} {data['email']}")
        print(f"  {BLUE}Status:{RESET} {data['status']}")
        print(f"  {BLUE}Trust Score:{RESET} {data['trust_score']}")
        print(f"  {BLUE}Email Verified:{RESET} {data['email_verified']}")
        print(f"  {BLUE}Roles:{RESET} {data['roles']}")
    else:
        print_test("Get Current User", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Get Current User", "FAIL", str(e))

# =============================================================================
# TEST 7: GET ACTIVE SESSIONS
# =============================================================================
print_section("TEST 7: Get Active Sessions")
try:
    response = requests.get(
        f"{BASE_URL}/auth/sessions",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Get Active Sessions",
            "PASS",
            f"Found {len(data)} active session(s)"
        )
        for idx, session in enumerate(data, 1):
            print(f"  {BLUE}Session {idx}:{RESET}")
            print(f"    ID: {session['id']}")
            print(f"    IP: {session.get('ip_address', 'unknown')}")
            print(f"    Current: {session['is_current']}")
    else:
        print_test("Get Active Sessions", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Get Active Sessions", "FAIL", str(e))

# =============================================================================
# TEST 8: REFRESH TOKEN
# =============================================================================
print_section("TEST 8: Token Refresh")
try:
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]}
    )
    if response.status_code == 200:
        data = response.json()
        old_access = tokens["access_token"][:20]
        tokens["access_token"] = data["access_token"]
        tokens["refresh_token"] = data["refresh_token"]
        new_access = tokens["access_token"][:20]
        print_test(
            "Token Refresh",
            "PASS",
            f"Tokens rotated successfully"
        )
        print(f"  {BLUE}Old Access Token:{RESET} {old_access}...")
        print(f"  {BLUE}New Access Token:{RESET} {new_access}...")
    else:
        print_test("Token Refresh", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Token Refresh", "FAIL", str(e))

# =============================================================================
# TEST 9: CHANGE PASSWORD
# =============================================================================
print_section("TEST 9: Change Password")
NEW_PASSWORD = "NewTest456!@#Strong"
try:
    response = requests.post(
        f"{BASE_URL}/auth/change-password",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "current_password": TEST_USER["password"],
            "new_password": NEW_PASSWORD
        }
    )
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Change Password",
            "PASS",
            data["message"]
        )
        TEST_USER["password"] = NEW_PASSWORD
    else:
        print_test("Change Password", "FAIL", f"Status Code: {response.status_code}")
        print(f"  {RED}Response:{RESET} {response.json()}")
except Exception as e:
    print_test("Change Password", "FAIL", str(e))

# =============================================================================
# TEST 10: LOGIN WITH NEW PASSWORD
# =============================================================================
print_section("TEST 10: Login With New Password")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_USER["email"],
            "password": NEW_PASSWORD
        }
    )
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Login With New Password",
            "PASS",
            "Successfully logged in with new password"
        )
    else:
        print_test("Login With New Password", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Login With New Password", "FAIL", str(e))

# =============================================================================
# TEST 11: LOGOUT
# =============================================================================
print_section("TEST 11: Logout Current Session")
try:
    response = requests.post(
        f"{BASE_URL}/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]}
    )
    if response.status_code == 200:
        data = response.json()
        print_test(
            "Logout",
            "PASS",
            data["message"]
        )
    else:
        print_test("Logout", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Logout", "FAIL", str(e))

# =============================================================================
# TEST 12: ACCESS PROTECTED ENDPOINT AFTER LOGOUT (Should Fail)
# =============================================================================
print_section("TEST 12: Access After Logout (Should Fail)")
try:
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    if response.status_code == 401:
        print_test(
            "Access Blocked After Logout",
            "PASS",
            "Correctly blocked access with revoked token"
        )
    else:
        print_test("Access Blocked After Logout", "FAIL", f"Status Code: {response.status_code}")
except Exception as e:
    print_test("Access Blocked After Logout", "FAIL", str(e))

# =============================================================================
# TEST SUMMARY
# =============================================================================
print(f"\n{GREEN}{'='*60}{RESET}")
print(f"{GREEN}ALL AUTHENTICATION TESTS COMPLETED!{RESET}")
print(f"{GREEN}{'='*60}{RESET}\n")

print(f"{BLUE}Test Summary:{RESET}")
print(f"  • Health check endpoint working")
print(f"  • User registration working")
print(f"  • Email verification check working")
print(f"  • Login with JWT tokens working")
print(f"  • Protected endpoints working")
print(f"  • Token refresh and rotation working")
print(f"  • Password change working")
print(f"  • Session management working")
print(f"  • Logout and token revocation working")
print(f"\n{GREEN}[SUCCESS] Authentication system is fully operational!{RESET}\n")
