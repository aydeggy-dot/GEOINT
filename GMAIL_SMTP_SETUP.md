# Gmail SMTP Setup Guide (2 Minutes!)

## Quick Setup Steps:

### 1. Enable 2-Factor Authentication on Your Gmail Account
1. Go to https://myaccount.google.com/security
2. Click on "2-Step Verification"
3. Follow the prompts to enable it (required for App Passwords)

### 2. Create an App Password
1. Go to https://myaccount.google.com/apppasswords
2. In the "Select app" dropdown, choose "Mail"
3. In the "Select device" dropdown, choose "Other (Custom name)"
4. Enter "Nigeria Security EWS"
5. Click "Generate"
6. **Copy the 16-character password** (you won't see it again!)

### 3. Configure Your Application

Add these environment variables to DigitalOcean:

```
GMAIL_EMAIL = your-gmail-address@gmail.com
GMAIL_APP_PASSWORD = xxxx xxxx xxxx xxxx (the 16-char password from step 2)
EMAIL_FROM_NAME = Nigeria Security EWS
USE_GMAIL = true
```

### 4. Update Backend Configuration

The backend needs a small modification to use Gmail instead of Brevo.

## Limitations:

- **500 emails per day** (should be enough for proof of concept)
- Gmail footer added to emails
- Not recommended for production at scale

## Advantages:

- ✅ Works immediately, no verification delays
- ✅ Free
- ✅ Easy setup
- ✅ Perfect for testing and proof of concept

## Alternative Options If You Need More:

1. **SendGrid** - 100 emails/day free (faster verification than Brevo)
2. **Mailgun** - 5000 emails/month for first 3 months
3. **SMTP2GO** - 1000 emails/month free

---

## Testing:

After configuration, test locally:
```bash
set GMAIL_EMAIL=your-email@gmail.com
set GMAIL_APP_PASSWORD=your-app-password
set USE_GMAIL=true
python test_email_gmail.py
```
