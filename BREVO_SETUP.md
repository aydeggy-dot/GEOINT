# Brevo Email Service Setup Guide

## Getting Your API Key

1. Log in to Brevo at https://app.brevo.com/
2. Click on your name in the top right
3. Go to **SMTP & API** section
4. Click on **API Keys** tab
5. Click **Generate a new API key**
6. Give it a name (e.g., "Nigeria Security EWS Production")
7. Copy the API key (you won't be able to see it again!)

## Verify Sender Email (Important!)

Before you can send emails, you must verify your sender domain or email:

1. Go to **Senders** section in Brevo
2. Click **Add a new sender**
3. Enter your email address (or use a custom domain)
4. Verify the email by clicking the link sent to your inbox

**Note:** Free plan allows up to 300 emails per day.

## Configure Production Environment

Once you have your API key, add it to DigitalOcean:

1. Go to your app in DigitalOcean dashboard
2. Click on **Settings** tab
3. Scroll to **App-Level Environment Variables**
4. Click **Edit**
5. Add these variables:
   - `BREVO_API_KEY`: Your Brevo API key
   - `EMAIL_FROM_ADDRESS`: Your verified sender email
   - `EMAIL_FROM_NAME`: Nigeria Security EWS

6. Click **Save**
7. Redeploy the app

## What Emails Does the System Send?

1. **Email Verification** - When users register
2. **Password Reset** - When users request password reset
3. **Security Alerts** - Incident notifications (if configured)

## Testing Email Functionality

After setup, test by:
1. Registering a new user
2. Check that verification email arrives
3. Click the verification link
4. Try password reset flow
