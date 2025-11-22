# Authentication System - Changes Summary

## Key Changes Based on Requirements

### ✅ Cost-Saving Updates: NO SMS for Authentication

**What Changed:**
- **Registration**: Email + password (no SMS verification)
- **2FA**: Removed SMS-based 2FA entirely
- **Password Reset**: Email-only (no SMS option)
- **Notifications**: Email-first for all security alerts

**SMS Only Used For:**
- Optional incident alerts (for users who voluntarily add phone numbers)
- Africa's Talking used only for incident notifications, not authentication

---

## Updated Authentication Flow

### 1. User Registration (Self-Onboarding)
```
User → Enter Email + Password → Email Sent with Verification Link
→ Click Link → Account Activated → Login
```

**Details:**
- Email verification link valid for 24 hours
- Account inactive until email verified
- Phone number is optional (only for receiving SMS incident alerts)
- No SMS costs during registration

---

### 2. Two-Factor Authentication (2FA)

**Available Methods (SMS removed):**

#### ✅ Method 1: Authenticator App (TOTP) - Recommended
- Google Authenticator, Authy, Microsoft Authenticator
- 6-digit code, 30-second rotation
- Works offline
- Most secure option
- **FREE** - no costs

#### ✅ Method 2: Email-Based - Alternative
- 6-digit code sent to email
- Valid for 10 minutes
- Fallback if authenticator unavailable
- **FREE** - uses email service already needed

**Backup Codes:**
- 10 single-use codes generated during setup
- Downloadable/printable
- Use when device lost

**Mandatory 2FA:**
- Super Admins: Required (TOTP recommended)
- Admins: Required (TOTP recommended)
- Moderators: Required
- Analysts: Required
- Verified Reporters: Recommended
- Regular Users: Optional

---

### 3. Password Recovery
```
User → Enter Email → Reset Link Sent → Click Link → Enter New Password
→ Password Changed → All Sessions Logged Out → Login
```

**Security:**
- Reset link valid for 1 hour
- Single-use token
- Rate limit: 3 requests/hour
- Email notification on password change

---

## Email Service Requirements

**Critical Service Needed:**
Since email is now the primary authentication method, a reliable email service is essential.

**Recommended Options:**

### Option 1: SendGrid (Recommended)
- **Free Tier**: 100 emails/day
- **Paid**: $19.95/month for 50K emails
- **Pros**: Easy setup, great deliverability, Nigerian support
- **Best for**: Production systems

### Option 2: AWS SES
- **Cost**: $0.10 per 1,000 emails
- **Pros**: Very cheap, scalable, AWS integration
- **Cons**: Requires AWS account, more setup

### Option 3: Mailgun
- **Free Tier**: 100 emails/day for 3 months
- **Paid**: $35/month for 50K emails
- **Pros**: Good API, reliable

### Option 4: SMTP (Gmail Business/Custom)
- **Cost**: Varies (Gmail Workspace: $6/user/month)
- **Pros**: Simple setup
- **Cons**: Lower limits, can be flagged as spam

**Recommendation**: Start with **SendGrid** - industry standard for transactional emails.

---

## Cost Analysis

### Before (SMS-based):
- Registration: ~₦50 per SMS × 1000 users = ₦50,000/month
- 2FA: ~₦50 per SMS × 2 per login × 500 logins/day = ₦1,500,000/month
- Password reset: ~₦50 per SMS × 100 resets/day = ₦150,000/month
- **Total: ~₦1,700,000/month ($2,125 USD)**

### After (Email-based):
- SendGrid: $19.95/month (₦32,000)
- Registration: FREE (email)
- 2FA: FREE (TOTP app or email)
- Password reset: FREE (email)
- **Total: ~₦32,000/month ($40 USD)**

### 💰 Savings: ~₦1,668,000/month (~$2,085 USD/month)

**SMS Still Available For:**
- Incident alerts (optional, user-initiated)
- Estimated: 1,000 SMS/day × ₦50 = ₦50,000/month
- Only charged when actually used

**Total Authentication Cost: ~₦82,000/month ($102 USD) vs ₦1,750,000/month**

---

## Phone Number Handling

**New Approach:**
- Phone number is **optional** during registration
- Stored for SMS incident alerts only (not authentication)
- Users can add/update phone in profile settings
- Phone verification not required

**User Profile Fields:**
- Email (required, verified)
- Password (required, hashed)
- Name (optional)
- Phone (optional, for SMS alerts)
- Location (optional, for proximity alerts)

---

## Database Schema Changes

### `users` Table
```sql
-- Updated fields
email VARCHAR(255) NOT NULL UNIQUE,        -- Required, replaces phone as primary
password_hash VARCHAR(255) NOT NULL,       -- Required
email_verified BOOLEAN DEFAULT false,      -- Must verify email
phone_number VARCHAR(20),                  -- Optional (not unique anymore)
phone_verified BOOLEAN DEFAULT false,      -- Optional verification
```

### `verification_codes` Table
```sql
-- Updated to email-only
email VARCHAR(255),                        -- Email where code sent
type VARCHAR(50),                          -- 'email_verification', '2fa_email', 'password_reset'
code VARCHAR(10),                          -- 6-digit code or token
```

---

## Updated API Endpoints

### Authentication
```
POST   /api/v1/auth/register                 - Email + password
POST   /api/v1/auth/login                    - Email + password
GET    /api/v1/auth/verify-email/:token      - Click link in email
POST   /api/v1/auth/resend-verification      - Resend verification email
POST   /api/v1/auth/forgot-password          - Send reset link via email
POST   /api/v1/auth/reset-password           - Reset with token
```

### 2FA (No SMS)
```
POST   /api/v1/auth/2fa/enable               - Enable TOTP or email 2FA
POST   /api/v1/auth/2fa/verify               - Verify 2FA code
POST   /api/v1/auth/2fa/generate-backup-codes - Get backup codes
```

---

## Security Notifications (All via Email)

**Events Triggering Email Alerts:**
- Login from new device
- Login from new country
- Password changed
- 2FA enabled/disabled
- Email address changed (sent to old + new)
- Account suspended
- Role changed by admin
- 5+ failed login attempts

---

## Incident Alerts (Optional SMS)

**How It Works:**
1. User optionally adds phone number in profile
2. Enables "SMS alerts" in preferences
3. When incident verified nearby, receives:
   - Email (always)
   - SMS (only if phone number added and opted in)

**Cost Control:**
- SMS only sent to opted-in users
- User can disable SMS anytime
- Email alerts always sent (free)

---

## Migration Path

If implementing on existing system with phone-based users:

1. **Add email field** to all users (mark as required)
2. **Prompt existing users** to add email on next login
3. **Grace period**: Allow 30 days for email addition
4. **After 30 days**: Require email for login
5. **Phone numbers**: Convert to optional field for alerts

---

## Implementation Priority

### Phase 1: Email Authentication (Week 1-2)
- Email-based registration
- Email verification flow
- Login with email + password
- Password reset via email

### Phase 2: Email 2FA (Week 2-3)
- Email-based 2FA
- TOTP (Authenticator app) setup
- Backup codes
- 2FA enforcement for admin roles

### Phase 3: Security Features (Week 3-4)
- Email notifications for security events
- Session management
- Rate limiting
- Account lockout

### Phase 4: Optional SMS Alerts (Week 4)
- Add phone number to profile (optional)
- SMS alert preferences
- Incident SMS notifications
- Cost tracking

---

## Next Steps

1. ✅ **Choose email service** (Recommend: SendGrid)
2. ✅ **Get API keys** for email service
3. ✅ **Review updated design** (ADMIN_USER_SYSTEM_DESIGN.md)
4. ✅ **Approve changes**
5. ▶️ **Begin implementation**

---

## Questions Answered

**Q: Should we use SMS for verification?**
A: ✅ No - Using email only (cost savings)

**Q: What about 2FA?**
A: ✅ TOTP (Authenticator apps) + Email-based (no SMS)

**Q: Can users still get SMS alerts?**
A: ✅ Yes - Optional for incident alerts only (they add phone number themselves)

**Q: What's the cost savings?**
A: ✅ ~₦1,668,000/month (~$2,085 USD/month) saved

---

## Ready to Implement?

The design is now updated and cost-optimized. Shall I proceed with implementing:
1. Backend authentication system (email-based)
2. Frontend registration/login pages
3. Email service integration
4. 2FA with TOTP and email
5. Admin panel with RBAC

Let me know which phase to start with!
