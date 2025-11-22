# Nigeria Security EWS - Admin & User Management System Design

## Executive Summary

This document outlines a comprehensive user management, authentication, and authorization system for the Nigeria Security Early Warning System. The system handles sensitive security data and requires robust role-based access control (RBAC), audit logging, and multi-factor authentication.

---

## 1. User Types & Roles

### 1.1 Public Users (Unauthenticated)
**Access Level**: Read-only, limited features

**Can Access**:
- ✅ View incident map (all verified incidents)
- ✅ View dashboard statistics
- ✅ Browse incident list (verified only)
- ✅ View verified incident details
- ✅ Search nearby incidents
- ✅ Export verified incidents to CSV
- ❌ Cannot report incidents
- ❌ Cannot see unverified incidents
- ❌ Cannot see reporter information

**Use Case**: General public, researchers, journalists, concerned citizens

---

### 1.2 Registered Users (Authenticated Citizens)
**Access Level**: Read + Limited Write

**Can Access**:
- ✅ All public features
- ✅ **Report new incidents** (anonymous or identified)
- ✅ View their own submission history
- ✅ Edit their own pending/unverified reports
- ✅ Upload media files (photos, videos)
- ✅ Set alert preferences (receive SMS/email for nearby incidents)
- ✅ View their trust score
- ✅ Manage profile (phone, email, location)
- ✅ Enable/disable 2FA
- ❌ Cannot verify incidents
- ❌ Cannot edit others' reports
- ❌ Cannot delete incidents
- ❌ Cannot access admin panel

**Use Case**: Citizens who want to report incidents and receive alerts

**Registration Requirements**:
- Phone number (required, for SMS verification)
- Email (optional, but recommended for 2FA)
- Name (optional, supports anonymous reporting)
- Location (optional, for proximity alerts)

---

### 1.3 Verified Reporters (Trusted Citizens)
**Access Level**: Enhanced reporting privileges

**Can Access**:
- ✅ All Registered User features
- ✅ **Higher trust score** (reports marked as more credible)
- ✅ Reports auto-verified if trust score > 0.8
- ✅ Priority in incident feed
- ✅ Badge/indicator showing "Verified Reporter" status
- ✅ View verification statistics dashboard
- ✅ Access to reporter training materials
- ❌ Still cannot verify others' reports
- ❌ Cannot access admin functions

**Use Case**: Community leaders, NGO workers, journalists, frequent accurate reporters

**How to Become Verified**:
- Minimum 10 submitted reports
- At least 70% verification rate
- Manual approval by Admin/Moderator
- OR: Pre-verified by partner organizations (Red Cross, NGOs)

---

### 1.4 Moderators (Field Coordinators)
**Access Level**: Verification & content moderation

**Can Access**:
- ✅ All Verified Reporter features
- ✅ **Verify/reject submitted incidents**
- ✅ Edit incident details (description, location, severity)
- ✅ Add verification notes
- ✅ View reporter information (phone numbers, history)
- ✅ Assign incidents to field teams
- ✅ Update casualty numbers
- ✅ Add tags and categorize incidents
- ✅ View unverified incidents queue
- ✅ Bulk operations (verify multiple, export filtered)
- ✅ Send alerts to specific regions
- ❌ Cannot delete incidents
- ❌ Cannot manage users
- ❌ Cannot access system settings
- ❌ Limited admin panel access

**Use Case**: NEMA coordinators, state emergency officers, NGO field staff

**Assignment**: Assigned by Admins, typically region-specific

---

### 1.5 Analysts (Intelligence Officers)
**Access Level**: Read-all + reporting

**Can Access**:
- ✅ View ALL incidents (verified and unverified)
- ✅ Advanced analytics dashboard
- ✅ Trend analysis tools
- ✅ Export comprehensive reports
- ✅ Create custom dashboards
- ✅ Access to full incident timeline
- ✅ View reporter trust scores and patterns
- ✅ Geospatial analysis tools
- ✅ Download bulk data (JSON, CSV, GeoJSON)
- ✅ API access for integrations
- ❌ Cannot verify/reject incidents
- ❌ Cannot edit incident content
- ❌ Cannot manage users

**Use Case**: Security analysts, intelligence officers, research institutions

---

### 1.6 Administrators (System Admins)
**Access Level**: Full control

**Can Access**:
- ✅ **ALL system features**
- ✅ User management (create, edit, delete, assign roles)
- ✅ Delete incidents (with audit trail)
- ✅ System configuration
- ✅ Manage moderators and analysts
- ✅ View audit logs
- ✅ Promote users to Verified Reporter
- ✅ Ban/suspend users
- ✅ Manage alert systems
- ✅ Database backups
- ✅ API key management
- ✅ Integration settings
- ✅ View system health metrics

**Use Case**: IT staff, system administrators, senior government officials

**Security**: Requires mandatory 2FA, IP whitelisting recommended

---

### 1.7 Super Admin (Root Access)
**Access Level**: Unrestricted

**Can Access**:
- ✅ All Administrator features
- ✅ **Manage other administrators**
- ✅ Change system-wide security settings
- ✅ Access server logs
- ✅ Emergency system shutdown
- ✅ Restore deleted data
- ✅ Override any permission

**Use Case**: Lead IT officer, designated government authority

**Security**: Requires 2FA + hardware security key, all actions logged

---

## 2. Permissions Matrix

| Feature                          | Public | User | Verified | Moderator | Analyst | Admin | Super |
|----------------------------------|--------|------|----------|-----------|---------|-------|-------|
| View verified incidents          | ✅     | ✅   | ✅       | ✅        | ✅      | ✅    | ✅    |
| View unverified incidents        | ❌     | ❌   | ❌       | ✅        | ✅      | ✅    | ✅    |
| Report incident                  | ❌     | ✅   | ✅       | ✅        | ✅      | ✅    | ✅    |
| Edit own report                  | ❌     | ✅   | ✅       | ✅        | ✅      | ✅    | ✅    |
| Edit any incident                | ❌     | ❌   | ❌       | ✅        | ❌      | ✅    | ✅    |
| Verify incident                  | ❌     | ❌   | ❌       | ✅        | ❌      | ✅    | ✅    |
| Delete incident                  | ❌     | ❌   | ❌       | ❌        | ❌      | ✅    | ✅    |
| View reporter info               | ❌     | Own  | Own      | ✅        | ✅      | ✅    | ✅    |
| Manage users                     | ❌     | ❌   | ❌       | ❌        | ❌      | ✅    | ✅    |
| View audit logs                  | ❌     | Own  | Own      | Own       | Own     | ✅    | ✅    |
| System settings                  | ❌     | ❌   | ❌       | ❌        | ❌      | ✅    | ✅    |
| Manage admins                    | ❌     | ❌   | ❌       | ❌        | ❌      | ❌    | ✅    |
| Export data                      | Verified| Verified| Verified | ✅     | ✅      | ✅    | ✅    |
| Send alerts                      | ❌     | ❌   | ❌       | ✅        | ❌      | ✅    | ✅    |
| API access                       | ❌     | ❌   | ❌       | ❌        | ✅      | ✅    | ✅    |

---

## 3. Authentication & Security Features

### 3.1 User Registration (Self-Onboarding)

**Registration Flow**:
```
1. User visits /register
2. Provides email + password
3. System sends email verification link with token
4. User clicks link in email
5. Email verified, account activated
6. Optional: Add name, phone number, location
7. Account created (role: Registered User)
8. Redirected to dashboard
```

**Password Requirements**:
- Minimum 8 characters
- Must include: uppercase, lowercase, number, special character
- Cannot be common passwords (check against database)
- Hashed with bcrypt (cost factor: 12)

**Email Verification**:
- Verification link sent via email (SMTP/SendGrid/AWS SES)
- Token valid for 24 hours
- Link format: `/verify-email?token=xxx`
- Max 3 verification email requests per hour
- Can resend verification email
- Account inactive until email verified

**Phone Number** (Optional):
- Users can optionally add phone number for SMS alerts
- Phone not required for registration
- If added, used only for receiving incident alerts (via Africa's Talking)

---

### 3.2 Two-Factor Authentication (2FA)

**Available Methods**:

#### Method 1: Authenticator App (TOTP) - Recommended
- Google Authenticator, Authy, Microsoft Authenticator
- Time-based One-Time Password (TOTP)
- 6-digit code, 30-second window
- Most secure option
- Works offline
- Backup codes provided (10 single-use codes)

#### Method 2: Email-Based - Alternative
- 6-digit code sent to verified email address
- Valid for 10 minutes
- Fallback option if authenticator app unavailable
- Less secure than TOTP (email account could be compromised)

**Setup Flow**:
```
1. User goes to Settings > Security
2. Click "Enable 2FA"
3. Choose method:
   - Authenticator App: Scan QR code with Google Authenticator/Authy
   - Email: Receive codes via email
4. Enter verification code to confirm setup
5. Download and save 10 backup codes (single-use)
6. 2FA enabled
```

**Login with 2FA**:
```
1. Enter email + password
2. System prompts for 2FA code
3. Options:
   - Enter code from authenticator app
   - Click "Send code to email" (if email method)
   - Use backup code (if lost device)
4. Enter 2FA code within time limit
5. Access granted
```

**Mandatory 2FA**:
- Super Admins: Required (TOTP strongly recommended)
- Admins: Required (TOTP strongly recommended)
- Moderators: Required
- Analysts: Required
- Verified Reporters: Recommended
- Regular Users: Optional

**Backup Codes**:
- 10 single-use codes generated during setup
- Each code can only be used once
- Downloadable as text file or printable
- Can regenerate new set (invalidates old codes)
- Used when authenticator device is lost/unavailable

---

### 3.3 Session Management

**JWT Token Strategy**:
- Access Token: 15 minutes (short-lived)
- Refresh Token: 7 days (httpOnly cookie)
- Stored in httpOnly, Secure, SameSite=Strict cookies

**Token Payload**:
```json
{
  "user_id": "uuid",
  "role": "moderator",
  "permissions": ["verify_incident", "edit_incident"],
  "trust_score": 0.85,
  "iat": 1234567890,
  "exp": 1234567890
}
```

**Session Features**:
- Remember Me: Refresh token valid for 30 days
- Logout: Invalidate both tokens, blacklist refresh token
- Logout All Devices: Invalidate all user sessions
- View Active Sessions: See all logged-in devices/locations
- Auto-logout: After 30 minutes of inactivity

---

### 3.4 Password Recovery

**Forgot Password Flow**:
```
1. User clicks "Forgot Password"
2. Enter email address
3. System sends password reset link to email
4. User clicks link (valid for 1 hour)
5. Redirected to reset password page
6. Enter new password (confirm)
7. Password updated
8. All sessions logged out (security measure)
9. Redirect to login with success message
```

**Security Measures**:
- Reset link contains unique token (JWT signed)
- Token valid for 1 hour only
- Single-use token (invalidated after password change)
- Max 3 reset requests per hour per email
- Rate limiting prevents brute force
- Old password cannot be reused (check last 5 passwords)
- Email notification sent confirming password change

---

### 3.5 Account Security Features

**Login Security**:
- Captcha after 3 failed login attempts
- Account locked after 5 failed attempts (15 minutes)
- Email notification on new device login
- Email notification on login from new country/IP
- Geographic anomaly detection (login from new country)

**Account Lockout**:
- Temporary: 15 minutes (5 failed logins)
- Admin suspension: Until admin review
- Permanent ban: Requires Super Admin approval

**Security Events Triggering Email Alerts**:
- Login from new device
- Login from new IP/country
- Password changed
- 2FA disabled
- Email address changed (sent to old and new email)
- Role changed (by admin)
- Account suspended/banned
- Failed login attempts (5+ attempts)

---

## 4. Admin Panel Features

### 4.1 Admin Dashboard

**Overview Metrics**:
- Total users (by role)
- Active users (last 24 hours)
- New registrations (last 7 days)
- Pending verifications (incidents awaiting review)
- Failed login attempts (last hour)
- System health status
- Storage usage
- API request volume

**Quick Actions**:
- Verify pending incidents
- Review flagged reports
- Manage user reports
- Send system-wide alert
- View recent audit logs

---

### 4.2 User Management

**User List** (`/admin/users`):
- Search by name, phone, email, role
- Filter by: role, trust score, active/inactive, region
- Sort by: registration date, last seen, trust score
- Pagination: 50 users per page
- Bulk actions: Export, send message, assign role

**User Details** (`/admin/users/:id`):
- Profile information
- Role and permissions
- Trust score history
- Submission history (all reports)
- Verification rate
- Login history (last 20 logins)
- Active sessions
- Audit log (actions taken on this user)

**User Actions**:
- Edit profile (name, email, phone)
- Change role (with confirmation)
- Promote to Verified Reporter
- Suspend account (temporary)
- Ban account (permanent, requires reason)
- Reset password (force password change on next login)
- Reset 2FA (if user lost device)
- View submitted incidents
- View received alerts
- Send direct message/alert

---

### 4.3 Incident Management

**Incident Queue** (`/admin/incidents/pending`):
- All unverified incidents
- Sortable by: date, severity, reporter trust score
- Filter by: state, incident type, severity
- Bulk verify/reject
- Assign to moderator
- Priority indicators (high severity + high trust score)

**Incident Verification** (`/admin/incidents/:id/verify`):
- View incident details
- View reporter history and trust score
- View attached media
- Edit details (location, description, severity, casualties)
- Add verification notes (internal, not public)
- Mark as verified, rejected, or duplicate
- Flag for review (escalate to senior moderator)
- Send feedback to reporter

**Incident Actions**:
- Edit any field
- Delete (soft delete with reason, restorable)
- Merge duplicates
- Change verification status
- Add tags
- Upload additional media
- View edit history (audit trail)
- Export incident report (PDF, JSON)

---

### 4.4 Role & Permission Management

**Role Management** (`/admin/roles`):
- View all roles and their permissions
- Create custom roles (e.g., "Regional Coordinator")
- Assign permissions to roles
- View users assigned to each role

**Permission Categories**:
- **Incidents**: view, create, edit, delete, verify
- **Users**: view, create, edit, delete, manage_roles
- **Alerts**: send, schedule, manage
- **Reports**: view, export, analyze
- **Settings**: view, edit
- **Audit**: view_logs, export_logs
- **System**: backup, restore, shutdown

**Role Assignment**:
- Assign role to user
- Temporary role elevation (e.g., "Analyst for 7 days")
- Auto-revoke after date
- Bulk role assignment (CSV upload)

---

### 4.5 Alert Management

**Send Alert** (`/admin/alerts/send`):
- Select recipients:
  - All users
  - Users in specific state(s)
  - Users within radius of location
  - Users with specific alert preferences
  - Individual users
- Alert type:
  - **SMS** (only for users who added phone numbers, via Africa's Talking)
  - **Email** (all users, primary method)
  - **Push Notification** (for mobile app users, future)
- Message content:
  - SMS: 160 characters max (for users with phone numbers)
  - Email: Full HTML/text formatting
- Schedule: Immediate or scheduled for later
- Preview before sending
- Cost estimate for SMS alerts

**Note**: SMS is used only for incident alerts, not for authentication. Users optionally add phone numbers to receive SMS incident alerts.

**Alert History** (`/admin/alerts/history`):
- All sent alerts
- Delivery status (sent, delivered, failed)
- Open/click rates (for emails)
- Filter by date, type, recipient count

**Alert Templates**:
- Pre-defined templates for common scenarios
- Variables: {incident_type}, {location}, {time}
- Example: "ALERT: {incident_type} reported in {location} at {time}. Stay safe."

---

### 4.6 Audit Logging

**Audit Log** (`/admin/audit`):
- All system actions with:
  - Timestamp
  - User (who performed action)
  - Action type (create, update, delete, login, etc.)
  - Resource (incident, user, setting)
  - Changes (before/after values)
  - IP address
  - User agent
- Filter by: user, action type, resource, date range
- Export audit logs (CSV, JSON)
- Retention: 2 years

**Logged Actions**:
- User login/logout
- Failed login attempts
- User registration
- Role changes
- Incident created/edited/deleted/verified
- Settings changed
- Alert sent
- User suspended/banned
- Password reset
- 2FA enabled/disabled
- Data exported
- Admin actions (all)

**Compliance**:
- Immutable logs (cannot be edited/deleted)
- Meets government audit requirements
- Supports forensic investigation

---

### 4.7 System Settings

**General Settings** (`/admin/settings/general`):
- Site name
- Contact email
- Default map center (Nigeria)
- Default time range for dashboards
- Timezone

**Security Settings** (`/admin/settings/security`):
- Enforce 2FA for roles
- Password policy
- Session timeout
- IP whitelist for admins
- Failed login threshold
- Account lockout duration

**Integration Settings** (`/admin/settings/integrations`):
- Africa's Talking API key
- Mapbox token
- Email service (SMTP)
- Backup settings (S3, local)
- Webhook URLs (for external systems)

**Alert Settings** (`/admin/settings/alerts`):
- Default alert radius
- SMS provider
- Email templates
- Push notification settings

---

## 5. User Features (Frontend)

### 5.1 User Dashboard (`/dashboard`)
- Welcome message with name
- Trust score badge
- Quick stats:
  - My reports: X submitted, Y verified, Z pending
  - Nearby incidents (last 7 days)
  - Active alerts in my region
- Quick actions:
  - Report new incident
  - View my reports
  - Manage alerts

### 5.2 My Reports (`/my-reports`)
- List of all submitted incidents
- Status indicators:
  - ✅ Verified (green)
  - ⏳ Pending (yellow)
  - ❌ Rejected (red with reason)
- Edit pending reports
- View verification notes (if rejected)

### 5.3 Alert Preferences (`/settings/alerts`)
- Enable/disable alerts
- Alert methods: SMS, Email, Push
- Set alert radius (10km - 500km)
- Filter by incident types
- Filter by severity levels
- Quiet hours (no alerts between 10 PM - 6 AM)

### 5.4 Account Settings (`/settings`)
- Profile: Name, email, phone, location
- Security: Password, 2FA, active sessions
- Privacy: Anonymous reporting preference
- Notifications: Email preferences
- Delete account (with confirmation)

### 5.5 Trust Score Dashboard (`/settings/trust-score`)
- Current trust score (0.0 - 1.0)
- Verification rate
- Reports submitted/verified/rejected
- Tips to improve trust score
- Verification badge (if Verified Reporter)

---

## 6. Workflow Examples

### 6.1 Citizen Reports Incident

```
1. Registered User logs in (with 2FA if enabled)
2. Navigates to "Report Incident"
3. Fills form:
   - Type: Armed Attack
   - Location: Click on map or enter address
   - Description: "Gunmen attacked village..."
   - Casualties: 5 killed, 10 injured
   - Upload photos/videos
   - Choose: Report as Anonymous (yes/no)
4. Submit report
5. Backend:
   - Checks user trust score
   - If trust_score > 0.8: Auto-verify
   - Else: Queue for moderator review
6. User receives confirmation email
   - SMS also sent if user added phone number
7. User can track status in "My Reports"
```

### 6.2 Moderator Verifies Incident

```
1. Moderator logs into admin panel
2. Navigates to "Pending Incidents" queue
3. Sorts by priority (high severity + reliable reporter)
4. Clicks incident to review:
   - Views reporter history (trust score 0.65)
   - Reviews description and photos
   - Checks location on map
   - Cross-references with other reports
5. Edits details (corrects casualty count)
6. Adds verification note: "Confirmed by local police"
7. Marks as "Verified"
8. Backend:
   - Incident now visible to public
   - Reporter's trust score increases
   - Reporter receives email: "Your report has been verified"
   - SMS also sent if reporter has phone number
   - Alert sent to nearby users (email/SMS based on preferences)
```

### 6.3 Admin Promotes User to Verified Reporter

```
1. Admin reviews user profile
2. Checks criteria:
   - 15 reports submitted ✅
   - 80% verification rate ✅
   - Active for 3+ months ✅
3. Clicks "Promote to Verified Reporter"
4. System:
   - Updates user role
   - Awards badge
   - Sends congratulations email
   - SMS also sent if user has phone number
   - Future reports auto-verified if trust > 0.8
5. Audit log records promotion
```

### 6.4 Admin Investigates Suspicious Activity

```
1. Admin receives alert: "5 failed login attempts for user X"
2. Navigates to user profile
3. Views audit log:
   - Failed logins from different countries
   - Unusual login times
4. Reviews user's recent reports:
   - Multiple reports from same location
   - All reports rejected as false
5. Decision: Suspend account
6. Adds suspension reason: "Suspicious activity investigation"
7. User receives email notification about suspension
   - SMS also sent if user has phone number
8. Admin can restore account after investigation
```

---

## 7. Database Schema Updates

### 7.1 New Tables Needed

#### `roles` Table
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- 'admin', 'moderator', etc.
    display_name VARCHAR(100),
    description TEXT,
    is_system_role BOOLEAN DEFAULT false, -- Cannot be deleted
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### `permissions` Table
```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- 'incident.verify', 'user.delete'
    resource VARCHAR(50), -- 'incident', 'user', 'setting'
    action VARCHAR(50), -- 'create', 'read', 'update', 'delete'
    description TEXT
);
```

#### `role_permissions` Table (Many-to-Many)
```sql
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);
```

#### `user_roles` Table (Many-to-Many)
```sql
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- NULL = permanent
    PRIMARY KEY (user_id, role_id)
);
```

#### `user_sessions` Table
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    refresh_token_hash VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB, -- Browser, OS, device type
    last_activity TIMESTAMP,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

#### `two_factor_auth` Table
```sql
CREATE TABLE two_factor_auth (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    method VARCHAR(20), -- 'sms', 'totp', 'email'
    secret VARCHAR(255), -- TOTP secret (encrypted)
    backup_codes TEXT[], -- Array of hashed backup codes
    enabled BOOLEAN DEFAULT false,
    enabled_at TIMESTAMP
);
```

#### `verification_codes` Table
```sql
CREATE TABLE verification_codes (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    code VARCHAR(10), -- 6-digit code or token
    type VARCHAR(50), -- 'email_verification', '2fa_email', 'password_reset'
    email VARCHAR(255), -- Email address where code was sent
    attempts INT DEFAULT 0,
    expires_at TIMESTAMP,
    used_at TIMESTAMP,
    created_at TIMESTAMP
);
```

#### `audit_logs` Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100), -- 'user.login', 'incident.verify'
    resource_type VARCHAR(50), -- 'user', 'incident'
    resource_id UUID,
    changes JSONB, -- Before/after values
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20), -- 'success', 'failure'
    error_message TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

#### `alerts` Table
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    title VARCHAR(200),
    message TEXT,
    type VARCHAR(20), -- 'sms', 'email', 'push'
    severity VARCHAR(20), -- 'info', 'warning', 'critical'
    sent_by UUID REFERENCES users(id),
    recipient_filter JSONB, -- Criteria for recipients
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    recipient_count INT,
    delivery_status JSONB, -- {sent: 100, delivered: 95, failed: 5}
    created_at TIMESTAMP
);
```

### 7.2 Updates to Existing Tables

#### `users` Table - Add Fields
```sql
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT true; -- After SMS verification
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'; -- 'active', 'suspended', 'banned'
ALTER TABLE users ADD COLUMN suspension_reason TEXT;
ALTER TABLE users ADD COLUMN suspended_until TIMESTAMP;
ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_ip INET;
ALTER TABLE users ADD COLUMN failed_login_attempts INT DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN registered_at TIMESTAMP DEFAULT NOW();
```

#### `incidents` Table - Add Fields
```sql
ALTER TABLE incidents ADD COLUMN verified_by UUID REFERENCES users(id);
ALTER TABLE incidents ADD COLUMN verified_at TIMESTAMP;
ALTER TABLE incidents ADD COLUMN verification_notes TEXT; -- Internal notes
ALTER TABLE incidents ADD COLUMN rejection_reason TEXT;
ALTER TABLE incidents ADD COLUMN flagged BOOLEAN DEFAULT false;
ALTER TABLE incidents ADD COLUMN flag_reason TEXT;
ALTER TABLE incidents ADD COLUMN edited_by UUID REFERENCES users(id);
ALTER TABLE incidents ADD COLUMN edit_count INT DEFAULT 0;
ALTER TABLE incidents ADD COLUMN deleted_at TIMESTAMP; -- Soft delete
ALTER TABLE incidents ADD COLUMN deleted_by UUID REFERENCES users(id);
ALTER TABLE incidents ADD COLUMN deletion_reason TEXT;
```

---

## 8. API Endpoints Summary

### Authentication Endpoints
```
POST   /api/v1/auth/register                 - Self-registration (email + password)
POST   /api/v1/auth/login                    - Login with email + password (returns JWT)
POST   /api/v1/auth/logout                   - Logout current session
POST   /api/v1/auth/refresh                  - Refresh access token
POST   /api/v1/auth/forgot-password          - Request password reset link (via email)
POST   /api/v1/auth/reset-password           - Reset password with token
GET    /api/v1/auth/me                       - Get current user profile
GET    /api/v1/auth/verify-email/:token      - Verify email address via link
POST   /api/v1/auth/resend-verification      - Resend email verification link
```

### 2FA Endpoints
```
POST   /api/v1/auth/2fa/enable               - Enable 2FA
POST   /api/v1/auth/2fa/disable              - Disable 2FA
POST   /api/v1/auth/2fa/verify               - Verify 2FA code during login
POST   /api/v1/auth/2fa/generate-backup-codes - Generate new backup codes
```

### User Management Endpoints
```
GET    /api/v1/users/me                      - Get own profile
PUT    /api/v1/users/me                      - Update own profile
DELETE /api/v1/users/me                      - Delete own account
GET    /api/v1/users/me/reports              - Get own reports
GET    /api/v1/users/me/sessions             - Get active sessions
DELETE /api/v1/users/me/sessions/:id         - Logout specific session
GET    /api/v1/users/me/audit-log            - Get own audit log
```

### Admin User Management Endpoints
```
GET    /api/v1/admin/users                   - List all users (paginated, filtered)
GET    /api/v1/admin/users/:id               - Get user details
PUT    /api/v1/admin/users/:id               - Update user
DELETE /api/v1/admin/users/:id               - Delete user
POST   /api/v1/admin/users/:id/suspend       - Suspend user
POST   /api/v1/admin/users/:id/ban           - Ban user
POST   /api/v1/admin/users/:id/activate      - Activate user
POST   /api/v1/admin/users/:id/assign-role   - Assign role
DELETE /api/v1/admin/users/:id/remove-role   - Remove role
POST   /api/v1/admin/users/:id/reset-password - Force password reset
POST   /api/v1/admin/users/:id/reset-2fa     - Reset 2FA
GET    /api/v1/admin/users/:id/audit-log     - Get user audit log
GET    /api/v1/admin/users/:id/sessions      - Get user sessions
```

### Admin Incident Management Endpoints
```
GET    /api/v1/admin/incidents/pending       - Get unverified incidents
POST   /api/v1/admin/incidents/:id/verify    - Verify incident
POST   /api/v1/admin/incidents/:id/reject    - Reject incident
POST   /api/v1/admin/incidents/:id/flag      - Flag for review
PUT    /api/v1/admin/incidents/:id           - Edit incident
DELETE /api/v1/admin/incidents/:id           - Soft delete
POST   /api/v1/admin/incidents/:id/restore   - Restore deleted incident
GET    /api/v1/admin/incidents/:id/history   - Get edit history
```

### Admin Role & Permission Endpoints
```
GET    /api/v1/admin/roles                   - List roles
GET    /api/v1/admin/roles/:id               - Get role details
POST   /api/v1/admin/roles                   - Create role
PUT    /api/v1/admin/roles/:id               - Update role
DELETE /api/v1/admin/roles/:id               - Delete role
GET    /api/v1/admin/permissions             - List permissions
POST   /api/v1/admin/roles/:id/permissions   - Assign permissions to role
```

### Admin Alert Endpoints
```
POST   /api/v1/admin/alerts/send             - Send alert
GET    /api/v1/admin/alerts                  - List sent alerts
GET    /api/v1/admin/alerts/:id              - Get alert details
GET    /api/v1/admin/alerts/:id/recipients   - Get recipient list
```

### Admin Audit Endpoints
```
GET    /api/v1/admin/audit-logs              - List audit logs (paginated, filtered)
GET    /api/v1/admin/audit-logs/export       - Export audit logs (CSV)
```

### Admin Settings Endpoints
```
GET    /api/v1/admin/settings                - Get all settings
PUT    /api/v1/admin/settings                - Update settings
GET    /api/v1/admin/system/health           - System health check
GET    /api/v1/admin/system/stats            - System statistics
```

---

## 9. Security Considerations

### 9.1 Data Protection
- **PII Encryption**: Phone numbers, emails encrypted at rest
- **Password Hashing**: bcrypt with cost factor 12
- **Token Security**: JWT signed with RS256 (public/private key)
- **HTTPS Only**: All traffic encrypted in transit
- **Database Encryption**: PostgreSQL encryption for sensitive columns

### 9.2 Rate Limiting
- Login attempts: 5 per minute per IP
- Registration: 3 per hour per IP
- SMS verification: 3 per hour per phone
- API requests: 100 per minute per user
- Export operations: 10 per hour per user

### 9.3 Input Validation
- SQL injection prevention (parameterized queries)
- XSS prevention (bleach library already in use)
- CSRF protection (SameSite cookies)
- File upload validation (type, size, virus scan)
- Phone number validation (Nigerian format)

### 9.4 Monitoring & Alerts
- Failed login patterns (brute force detection)
- Geographic anomalies (login from new country)
- Privilege escalation attempts
- Bulk data exports
- Unusual API usage patterns
- System health metrics (CPU, memory, disk)

---

## 10. Implementation Priority

### Phase 1: Core Authentication (Week 1-2)
1. ✅ Basic authentication (login/logout)
2. ✅ JWT token generation
3. ✅ User registration with phone verification
4. ✅ Password reset flow
5. ✅ Session management

### Phase 2: Role-Based Access Control (Week 3)
1. ✅ Role and permission system
2. ✅ Middleware for permission checks
3. ✅ Admin user management
4. ✅ Role assignment

### Phase 3: Two-Factor Authentication (Week 4)
1. ✅ SMS-based 2FA
2. ✅ TOTP (authenticator app) support
3. ✅ Backup codes
4. ✅ 2FA enforcement for admins

### Phase 4: Admin Panel - User Management (Week 5)
1. ✅ Admin dashboard
2. ✅ User list and search
3. ✅ User details and editing
4. ✅ Suspend/ban users
5. ✅ Role assignment UI

### Phase 5: Admin Panel - Incident Management (Week 6)
1. ✅ Pending incidents queue
2. ✅ Verification workflow
3. ✅ Edit incident details
4. ✅ Flag/reject incidents
5. ✅ Soft delete

### Phase 6: Audit Logging (Week 7)
1. ✅ Audit log infrastructure
2. ✅ Log all critical actions
3. ✅ Admin audit log viewer
4. ✅ Export audit logs
5. ✅ Retention policy

### Phase 7: Alerts & Notifications (Week 8)
1. ✅ Alert management system
2. ✅ Send alerts UI
3. ✅ Alert templates
4. ✅ Delivery tracking
5. ✅ User alert preferences

### Phase 8: Advanced Features (Week 9-10)
1. ✅ Trust score calculation improvements
2. ✅ Verified reporter promotion workflow
3. ✅ Custom roles
4. ✅ API key management for analysts
5. ✅ Advanced analytics for analysts

---

## 11. Questions to Resolve

1. **Email Service** (Critical): Which email service should be used for authentication, verification, and notifications?
   - Options: SendGrid, AWS SES, Mailgun, SMTP (Gmail, custom)
   - Requirements: High deliverability, support for transactional emails, affordable pricing
   - Needed for: Registration verification, password reset, 2FA, notifications

2. **SMS Provider** (Optional): Confirm Africa's Talking for incident alerts only?
   - SMS used only for incident alerts, not authentication (cost savings)
   - Only sent to users who optionally add phone numbers
   - Estimate monthly SMS volume for budgeting

3. **Admin Access**: How many super admins initially? Who will have root access?

4. **Verification SLA**: What's the expected time for moderators to verify incidents? (affects workload/staffing)

5. **Data Retention**: How long should we keep:
   - Audit logs? (Recommended: 2 years)
   - Deleted incidents? (Recommended: 90 days)
   - User sessions? (Recommended: 30 days)

6. **Geographic Scope**:
   - Should moderators be region-specific (e.g., "North-East Coordinator")?
   - Should we restrict login by IP ranges for admins?

7. **Integration Requirements**:
   - Need to integrate with existing government systems? (police database, NEMA, etc.)
   - API access for partner organizations? (Red Cross, UN agencies)

8. **Hardware Security Keys**:
   - Should we support YubiKey/FIDO2 for super admins?
   - Budget for hardware keys?

9. **Mobile App**:
   - Is a mobile app planned? (affects 2FA and push notification strategy)
   - React Native or separate native apps?

10. **Backup Strategy**:
    - Daily automated backups?
    - Offsite backup location?
    - Disaster recovery plan?

---

## 12. Estimated Effort

**Backend Development**: ~6-8 weeks (1 developer)
- Authentication & 2FA: 2 weeks
- RBAC & permissions: 1.5 weeks
- Admin APIs: 2 weeks
- Audit logging: 1 week
- Alert system: 1 week
- Testing & bug fixes: 1 week

**Frontend Development**: ~4-6 weeks (1 developer)
- Admin panel UI: 3 weeks
- User dashboard: 1 week
- Security features UI: 1 week
- Testing & polish: 1 week

**DevOps & Security**: ~1-2 weeks
- SSL/TLS setup
- Rate limiting
- Monitoring
- Backup automation

**Total**: ~10-12 weeks with 2 developers working in parallel

---

## Next Steps

1. **Review & Approve** this design document
2. **Answer the 10 questions** above
3. **Prioritize features** (if timeline is tight)
4. **Begin implementation** starting with Phase 1

Would you like me to proceed with implementing this system?
