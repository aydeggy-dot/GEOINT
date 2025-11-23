# Nigeria Security EWS - Cloud Deployment Guide

## Quick Summary

**Recommended Option for Cost-Effective Deployment: DigitalOcean**
- **Cost**: $40-80/month
- **Deployment Time**: 2-4 hours
- **Best For**: Production-ready with good balance of cost and features

**Fastest Option: Railway.app**
- **Cost**: $30-60/month
- **Deployment Time**: 30 minutes
- **Best For**: Quick deployment with minimal configuration

## Cloud Platform Comparison

| Platform | Monthly Cost | Deployment Time | Complexity | Best For |
|----------|-------------|-----------------|------------|----------|
| **Railway.app** | $30-60 | 30 min | Low | Fastest deployment |
| **DigitalOcean** | $40-80 | 2-4 hours | Medium | Best cost/features |
| **AWS (Lightsail)** | $50-100 | 4-6 hours | High | Enterprise scale |
| **Google Cloud** | $60-120 | 4-6 hours | High | Advanced features |
| **Azure** | $60-120 | 4-6 hours | High | Microsoft ecosystem |

## Cost Breakdown (DigitalOcean - Recommended)

### Infrastructure
- **App Platform (Backend)**: $12/month (Basic)
- **App Platform (Frontend)**: $5/month (Static site)
- **Managed PostgreSQL**: $15/month (1GB RAM, 10GB storage)
- **Managed Redis**: $15/month (1GB RAM)
- **Spaces (Object Storage)**: $5/month (250GB storage, 1TB transfer)
- **Total**: ~$52/month

### Scaling Options
- **Medium Scale** (~1,000 users): $80/month
- **Large Scale** (~10,000 users): $150-200/month

---

## Option 1: Railway.app (Fastest - 30 Minutes)

### Why Railway.app?
- One-click PostgreSQL and Redis
- Automatic HTTPS
- GitHub integration with auto-deploy
- Simple environment variables management
- Built-in monitoring

### Step-by-Step Deployment

#### 1. Prepare Your Code (5 minutes)

Create `railway.json` in project root:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

Create `Procfile` for backend:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 2. Deploy to Railway (10 minutes)

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `GEOINT` repository
4. Railway will detect your Python backend

#### 3. Add Database Services (5 minutes)

1. Click "New" → "Database" → "PostgreSQL"
2. Click "New" → "Database" → "Redis"
3. Railway automatically creates connection URLs

#### 4. Configure Environment Variables (5 minutes)

In your backend service settings, add:
```bash
DATABASE_URL=${RAILWAY_POSTGRES_URL}
REDIS_URL=${RAILWAY_REDIS_URL}
SECRET_KEY=generate-a-secure-random-key-here
FRONTEND_URL=https://your-app.up.railway.app
ENVIRONMENT=production
```

Generate SECRET_KEY:
```python
import secrets
print(secrets.token_urlsafe(32))
```

#### 5. Deploy Frontend (5 minutes)

1. Click "New" → "GitHub Repo" → Select your repo again
2. Set root directory: `frontend`
3. Build command: `npm run build`
4. Start command: `npm run preview`
5. Add environment variable:
```
VITE_API_BASE_URL=https://your-backend.up.railway.app/api/v1
```

#### 6. Configure Custom Domain (Optional)

1. Go to your frontend service settings
2. Click "Settings" → "Domains"
3. Add your custom domain (e.g., `security.example.com`)
4. Update DNS records as instructed

**Total Time**: ~30 minutes
**Monthly Cost**: $30-60

---

## Option 2: DigitalOcean (Recommended - Best Value)

### Why DigitalOcean?
- Excellent documentation
- Predictable pricing
- Managed databases
- App Platform (PaaS) simplifies deployment
- Good performance for the price

### Step-by-Step Deployment

#### 1. Create DigitalOcean Account (5 minutes)

1. Go to [digitalocean.com](https://digitalocean.com)
2. Sign up (use GitHub for easy integration)
3. Add payment method

#### 2. Create Managed PostgreSQL Database (10 minutes)

1. Click "Create" → "Databases" → "PostgreSQL"
2. Choose:
   - Version: PostgreSQL 15
   - Plan: Basic ($15/month - 1GB RAM, 10GB storage)
   - Data center: Choose closest to Nigeria (e.g., Frankfurt or London)
3. Wait 3-5 minutes for provisioning
4. Go to "Users & Databases" tab:
   - Create database: `nigeria_security`
   - Note down connection details

#### 3. Create Managed Redis (5 minutes)

1. Click "Create" → "Databases" → "Redis"
2. Choose:
   - Plan: Basic ($15/month - 1GB RAM)
   - Same data center as PostgreSQL
3. Note down connection URL

#### 4. Prepare Application for Deployment (15 minutes)

Create `.do/app.yaml` in project root:
```yaml
name: nigeria-security-ews
region: fra

databases:
  - name: postgres
    engine: PG
    production: true
  - name: redis
    engine: REDIS
    production: true

services:
  - name: backend
    github:
      repo: aydeggy-dot/GEOINT
      branch: main
      deploy_on_push: true
    source_dir: /backend

    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${postgres.DATABASE_URL}
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${redis.REDIS_URL}
      - key: SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: YOUR_SECRET_KEY_HERE
      - key: FRONTEND_URL
        scope: RUN_TIME
        value: https://nigeria-security-ews-frontend.ondigitalocean.app
      - key: ENVIRONMENT
        scope: RUN_TIME
        value: production

    build_command: pip install -r requirements.txt
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080

    health_check:
      http_path: /api/v1/health

    http_port: 8080
    instance_count: 1
    instance_size_slug: basic-xxs

  - name: frontend
    github:
      repo: aydeggy-dot/GEOINT
      branch: main
      deploy_on_push: true
    source_dir: /frontend

    envs:
      - key: VITE_API_BASE_URL
        scope: BUILD_TIME
        value: https://nigeria-security-ews-backend.ondigitalocean.app/api/v1

    build_command: npm install && npm run build

    static_sites:
      - name: frontend
        build_command: npm run build
        output_dir: dist
```

#### 5. Deploy to App Platform (20 minutes)

1. Click "Create" → "Apps" → "GitHub"
2. Select your repository
3. DigitalOcean will detect `.do/app.yaml` automatically
4. Review the configuration
5. Update environment variables with actual values
6. Click "Create Resources"
7. Wait 10-15 minutes for initial deployment

#### 6. Run Database Migrations (5 minutes)

1. Go to your backend app → "Console"
2. Run migrations:
```bash
cd backend
alembic upgrade head
```

Or use the console to run your initialization scripts:
```bash
python -c "from app.db.init_db import init_db; init_db()"
```

#### 7. Setup Object Storage for Media Files (10 minutes)

1. Click "Create" → "Spaces" (DigitalOcean's S3-compatible storage)
2. Choose:
   - Name: `nigeria-security-media`
   - Region: Same as your apps
   - CDN: Enabled
3. Create API Key:
   - Go to API → Spaces Keys
   - Generate new key
   - Note down Access Key and Secret Key

Update backend environment variables:
```bash
SPACES_BUCKET=nigeria-security-media
SPACES_REGION=fra1
SPACES_ENDPOINT=https://fra1.digitaloceanspaces.com
SPACES_KEY=your_access_key
SPACES_SECRET=your_secret_key
```

#### 8. Configure Custom Domain (15 minutes)

1. Go to your frontend app → "Settings" → "Domains"
2. Add custom domain: `security.yourdomain.com`
3. Update your DNS records:
   - Type: CNAME
   - Name: security
   - Value: `nigeria-security-ews-frontend.ondigitalocean.app`
4. SSL certificate automatically provisioned in 5-10 minutes

#### 9. Setup Monitoring & Alerts (10 minutes)

1. Enable App Platform metrics (included free)
2. Create alert policies:
   - Go to "Monitoring" → "Alerts"
   - Create policy for:
     - CPU usage > 80%
     - Memory usage > 80%
     - Response time > 2s
3. Add email for notifications

**Total Time**: 2-4 hours
**Monthly Cost**: $52-80

---

## Option 3: AWS (Enterprise Scale)

### Why AWS?
- Highly scalable
- Pay-as-you-go pricing
- Comprehensive services
- Best for long-term growth

### Quick Start with AWS Lightsail (Simplified AWS)

#### 1. Create Lightsail Instances (30 minutes)

1. Go to [AWS Lightsail](https://lightsail.aws.amazon.com)
2. Create PostgreSQL database:
   - Plan: $15/month (1GB RAM, 40GB storage)
   - Note connection details
3. Create application instance:
   - OS: Ubuntu 20.04
   - Plan: $10/month (1GB RAM)
   - Add startup script:

```bash
#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install nginx
apt-get install -y nginx

# Install PostgreSQL client
apt-get install -y postgresql-client

# Setup application directory
mkdir -p /var/www/nigeria-security
cd /var/www/nigeria-security

# Clone repository
git clone https://github.com/aydeggy-dot/GEOINT.git .
```

#### 2. Configure Application (45 minutes)

SSH into your instance:
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

Setup backend:
```bash
cd /var/www/nigeria-security/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://user:pass@your-lightsail-db:5432/nigeria_security
REDIS_URL=redis://localhost:6379
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
FRONTEND_URL=https://yourdomain.com
ENVIRONMENT=production
EOF

# Setup systemd service
sudo tee /etc/systemd/system/nigeria-backend.service > /dev/null <<EOF
[Unit]
Description=Nigeria Security Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/nigeria-security/backend
Environment="PATH=/var/www/nigeria-security/backend/venv/bin"
ExecStart=/var/www/nigeria-security/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable nigeria-backend
sudo systemctl start nigeria-backend
```

Setup frontend:
```bash
cd /var/www/nigeria-security/frontend

# Create .env.production
echo "VITE_API_BASE_URL=https://api.yourdomain.com/api/v1" > .env.production

# Build
npm install
npm run build

# Configure nginx
sudo tee /etc/nginx/sites-available/nigeria-security > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/nigeria-security/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/nigeria-security /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### 3. Setup SSL with Let's Encrypt (10 minutes)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**Total Time**: 4-6 hours
**Monthly Cost**: $50-100

---

## Security Hardening (Critical for Production)

### 1. Environment Variables

Never commit these to git:
```bash
# Backend .env
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
SECRET_KEY=very-long-random-string-at-least-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=https://yourdomain.com
ENVIRONMENT=production

# CORS settings
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# File upload
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "gif", "mp4"]
```

### 2. Database Security

```sql
-- Create read-only user for reporting
CREATE USER reporting_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE nigeria_security TO reporting_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reporting_user;

-- Enable row-level security
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;

-- Backup policy (automated on managed databases)
-- DigitalOcean: Automatic daily backups included
-- Railway: Automatic backups on paid plans
```

### 3. Application Security

Update `backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = ["https://yourdomain.com"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    CORS_ALLOW_CREDENTIALS: bool = True

    # HTTPS only in production
    SECURE_COOKIES: bool = True

    # Session settings
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

    class Config:
        env_file = ".env"
```

### 4. Frontend Security

Update `frontend/vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'X-XSS-Protection': '1; mode=block',
      'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    }
  }
})
```

### 5. API Rate Limiting

Already implemented in your backend, but verify settings:
```python
# app/middleware/rate_limit.py
# Current: 100 requests per minute per IP
# Production: Consider 60 requests per minute
```

---

## Monitoring & Logging

### 1. Application Monitoring (Free Tier Options)

**Sentry for Error Tracking**:
```bash
# Backend
pip install sentry-sdk[fastapi]
```

```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production",
)
```

**Frontend**:
```bash
npm install @sentry/react
```

```typescript
// src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production",
  tracesSampleRate: 0.1,
});
```

### 2. Uptime Monitoring

Use [UptimeRobot](https://uptimerobot.com) (Free):
- Monitor: `https://yourdomain.com/api/v1/health`
- Interval: 5 minutes
- Alerts: Email, SMS, Slack

### 3. Log Management

**For DigitalOcean/Railway**: Built-in log aggregation

**For AWS/Custom**: Use CloudWatch or Papertrail
```bash
# Install Papertrail
sudo apt-get install -y rsyslog-gnutls
# Configure as per Papertrail instructions
```

---

## Database Backups

### DigitalOcean Managed Database
- Automatic daily backups (7-day retention)
- Manual snapshots available
- Point-in-time recovery

### Railway.app
- Automatic backups on paid plans
- Volume snapshots available

### Manual Backup Script
```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgres"
mkdir -p $BACKUP_DIR

# Backup
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/backup_$DATE.sql

# Upload to cloud storage (DigitalOcean Spaces)
s3cmd put $BACKUP_DIR/backup_$DATE.sql.gz s3://nigeria-security-backups/

# Delete local backups older than 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Schedule with cron:
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup_database.sh
```

---

## Performance Optimization

### 1. Database Indexing

Run these on production database:
```sql
-- Already have these, verify they exist
CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp);
CREATE INDEX IF NOT EXISTS idx_incidents_state ON incidents(state);
CREATE INDEX IF NOT EXISTS idx_incidents_verified ON incidents(verified);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);

-- Add composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_incidents_state_verified
  ON incidents(state, verified);
CREATE INDEX IF NOT EXISTS idx_incidents_timestamp_verified
  ON incidents(timestamp DESC, verified);

-- Spatial index for location queries
CREATE INDEX IF NOT EXISTS idx_incidents_location
  ON incidents USING GIST(location);
```

### 2. Redis Caching

Update `backend/app/services/cache.py`:
```python
# Cache frequently accessed data
CACHE_TTL = {
    'incidents_list': 300,  # 5 minutes
    'statistics': 600,      # 10 minutes
    'user_profile': 1800,   # 30 minutes
}
```

### 3. Frontend Optimization

Build with optimizations:
```bash
# Already in package.json
npm run build
# Outputs optimized bundle to dist/
```

Enable gzip compression in nginx:
```nginx
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

---

## Cost Optimization

### 1. Start Small, Scale Up

**Phase 1 (0-100 users)**: ~$50/month
- DigitalOcean Basic plan
- 1 backend instance
- Basic PostgreSQL (1GB)
- Basic Redis (1GB)

**Phase 2 (100-1,000 users)**: ~$80/month
- Scale backend to 2GB RAM
- PostgreSQL 2GB RAM
- Redis 2GB RAM

**Phase 3 (1,000-10,000 users)**: ~$150/month
- Multiple backend instances (load balanced)
- PostgreSQL 4GB RAM
- Redis 4GB RAM
- CDN for static assets

### 2. Free Services to Use

- **Error Tracking**: Sentry (free tier: 5,000 events/month)
- **Uptime Monitoring**: UptimeRobot (free: 50 monitors)
- **SSL Certificates**: Let's Encrypt (free)
- **CDN**: Cloudflare (free tier available)
- **Email**: SendGrid (free: 100 emails/day)

### 3. Database Query Optimization

Monitor slow queries:
```sql
-- Enable slow query logging in PostgreSQL
ALTER DATABASE nigeria_security SET log_min_duration_statement = 1000;

-- View slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Update all environment variables
- [ ] Generate strong SECRET_KEY
- [ ] Configure CORS with production domains
- [ ] Review and test all API endpoints
- [ ] Run database migrations locally
- [ ] Build frontend locally to check for errors
- [ ] Update API URLs in frontend config

### During Deployment
- [ ] Create cloud account
- [ ] Setup managed PostgreSQL
- [ ] Setup managed Redis
- [ ] Deploy backend application
- [ ] Run database migrations
- [ ] Create initial admin user
- [ ] Deploy frontend application
- [ ] Configure custom domain
- [ ] Setup SSL certificates

### Post-Deployment
- [ ] Test all authentication flows (login, register, 2FA)
- [ ] Test incident reporting
- [ ] Test admin functionality
- [ ] Verify email notifications work
- [ ] Setup monitoring (Sentry, UptimeRobot)
- [ ] Configure backup schedule
- [ ] Test backup restoration
- [ ] Setup alerts for errors and downtime
- [ ] Document API endpoints
- [ ] Create runbook for common issues

### Security Audit
- [ ] Enable HTTPS only
- [ ] Configure security headers
- [ ] Review CORS settings
- [ ] Test rate limiting
- [ ] Verify file upload restrictions
- [ ] Check SQL injection protection
- [ ] Test XSS protection
- [ ] Review authentication flow
- [ ] Audit user permissions

---

## Quick Start: Deploy to Railway (Recommended for First Try)

If you want to deploy RIGHT NOW in the next 30 minutes:

1. **Sign up**: Go to [railway.app](https://railway.app), sign in with GitHub

2. **Deploy**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `aydeggy-dot/GEOINT`
   - Railway auto-detects Python

3. **Add databases**:
   - Click "New" → "PostgreSQL"
   - Click "New" → "Redis"

4. **Configure backend** (add these environment variables):
   ```
   DATABASE_URL=${RAILWAY_POSTGRES_URL}
   REDIS_URL=${RAILWAY_REDIS_URL}
   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
   FRONTEND_URL=<will get after frontend deploys>
   ENVIRONMENT=production
   ```

5. **Deploy frontend**:
   - Click "New" → "GitHub Repo" → Select GEOINT again
   - Root directory: `frontend`
   - Build: `npm run build`
   - Start: `npm run preview`
   - Environment variable:
     ```
     VITE_API_BASE_URL=<your-backend-url>/api/v1
     ```

6. **Initialize database**: In backend console:
   ```bash
   alembic upgrade head
   python -m app.scripts.init_db
   ```

7. **Done!** Your app is live at `https://your-app.up.railway.app`

---

## Support & Troubleshooting

### Common Issues

**Issue**: Database connection failed
- **Solution**: Check DATABASE_URL format, ensure database is running, verify firewall rules

**Issue**: Frontend can't connect to backend
- **Solution**: Verify VITE_API_BASE_URL is correct, check CORS settings in backend

**Issue**: 502 Bad Gateway
- **Solution**: Backend likely crashed, check logs for errors, verify environment variables

**Issue**: Slow response times
- **Solution**: Check database query performance, enable Redis caching, add database indexes

### Getting Help

- DigitalOcean: https://docs.digitalocean.com
- Railway: https://docs.railway.app
- FastAPI: https://fastapi.tiangolo.com
- React: https://react.dev

---

## Summary

For your Nigeria Security EWS application, I recommend:

**Best Overall**: **DigitalOcean App Platform**
- Cost: $50-80/month
- Deployment time: 2-4 hours
- Great balance of features, cost, and ease of use
- Managed databases with automatic backups
- Easy scaling as you grow

**Fastest Deploy**: **Railway.app**
- Cost: $30-60/month
- Deployment time: 30 minutes
- Perfect for getting live quickly
- Can migrate to DigitalOcean later if needed

**Next Steps**:
1. Choose your platform (Railway for speed, DigitalOcean for production)
2. Follow the step-by-step guide above
3. Complete the deployment checklist
4. Setup monitoring and backups
5. Test everything thoroughly
6. Go live!

Your application is production-ready. The code quality is good, security features are in place (2FA, rate limiting, audit logs), and the architecture supports scaling.
