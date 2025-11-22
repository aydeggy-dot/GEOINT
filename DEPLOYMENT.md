# Nigeria Security Early Warning System - Deployment Guide

This guide covers deployment of the Nigeria Security Early Warning System using Docker and docker-compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [Production Deployment](#production-deployment)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository

### System Requirements

- **Minimum**: 2 CPU cores, 4GB RAM, 20GB disk space
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB disk space
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

### External Services

- **Mapbox Account**: Required for map functionality
  - Sign up at https://www.mapbox.com/
  - Get your access token from the account dashboard

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nigeria-security-system
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
nano .env  # or use your preferred editor
```

**Required Variables to Update:**

```bash
# Set a secure PostgreSQL password
POSTGRES_PASSWORD=your_secure_password_here

# Generate a secure secret key (use openssl rand -hex 32)
SECRET_KEY=your_secret_key_here

# Add your Mapbox token
VITE_MAPBOX_TOKEN=pk.your_mapbox_token_here
```

### 3. Start the Application

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Initialize the Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# (Optional) Seed with sample data
docker-compose exec backend python -m app.scripts.seed_data
```

### 5. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Environment Configuration

### Complete Environment Variables

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=nigeria_security
POSTGRES_USER=postgres

# Backend Configuration
SECRET_KEY=your-secret-key-change-in-production
DEBUG=false
ALLOWED_ORIGINS=http://localhost,https://yourdomain.com
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/nigeria_security

# Frontend Configuration
VITE_MAPBOX_TOKEN=your_mapbox_token_here
VITE_API_URL=/api/v1

# Optional: Email/SMS Alerts
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key
```

### Generating Secure Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 32
```

## Production Deployment

### Domain and HTTPS Setup

#### 1. Update Allowed Origins

Edit `.env`:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 2. Add SSL/TLS with Let's Encrypt

Update `docker-compose.yml` to add a Certbot service and modify Nginx:

```yaml
services:
  # ... existing services ...

  certbot:
    image: certbot/certbot
    container_name: certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

  frontend:
    # ... existing config ...
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    ports:
      - "80:80"
      - "443:443"
```

Create SSL certificate:
```bash
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos --no-eff-email
```

#### 3. Update Nginx Configuration

Create `frontend/nginx-ssl.conf` with HTTPS redirect and SSL configuration.

### Cloud Deployment Options

#### AWS EC2

1. Launch an EC2 instance (t3.medium recommended)
2. Install Docker and docker-compose
3. Clone repository and configure environment
4. Set up security groups (ports 80, 443, 22)
5. Configure Elastic IP for static IP
6. Optional: Use RDS for PostgreSQL instead of container

#### DigitalOcean Droplet

1. Create a Droplet (4GB RAM recommended)
2. Use Docker marketplace image
3. Clone and configure as above
4. Add DigitalOcean Load Balancer for SSL termination

#### Azure Container Instances

1. Use Azure Database for PostgreSQL
2. Deploy backend and frontend as separate container instances
3. Configure Azure Application Gateway for routing

### Environment-Specific Settings

**Development**:
```bash
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002
```

**Staging**:
```bash
DEBUG=false
ALLOWED_ORIGINS=https://staging.yourdomain.com
```

**Production**:
```bash
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
```

## Security Considerations

### 1. Environment Variables

- **Never commit `.env` files** to version control
- Use Docker secrets or vault systems for sensitive data in production
- Rotate credentials regularly (every 90 days recommended)

### 2. Database Security

```bash
# Use strong passwords (minimum 32 characters)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restrict database access to backend service only
# In docker-compose.yml, don't expose port 5432 externally
```

### 3. API Security

- Enable rate limiting for public endpoints
- Implement authentication for write operations
- Use HTTPS only in production
- Keep ALLOWED_ORIGINS restrictive

### 4. Container Security

```bash
# Scan images for vulnerabilities
docker scan nigeria-security-api:latest
docker scan nigeria-security-frontend:latest

# Update base images regularly
docker-compose pull
docker-compose up -d --build
```

### 5. Nginx Security Headers

The included `nginx.conf` already sets:
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

For production, add:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.mapbox.com;" always;
```

## Monitoring and Maintenance

### Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' nigeria-security-api
```

### Logging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Export logs to file
docker-compose logs --no-color > logs/app-$(date +%Y%m%d).log
```

### Performance Monitoring

```bash
# Monitor container resource usage
docker stats

# PostgreSQL connection monitoring
docker-compose exec postgres psql -U postgres -d nigeria_security \
  -c "SELECT count(*) as connections FROM pg_stat_activity;"

# Check database size
docker-compose exec postgres psql -U postgres -d nigeria_security \
  -c "SELECT pg_size_pretty(pg_database_size('nigeria_security'));"
```

### Updates and Patches

```bash
# Pull latest code
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

## Backup and Recovery

### Database Backup

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker-compose exec -T postgres pg_dump -U postgres nigeria_security \
  | gzip > backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Automated daily backups (add to crontab)
0 2 * * * cd /path/to/nigeria-security-system && \
  docker-compose exec -T postgres pg_dump -U postgres nigeria_security \
  | gzip > backups/backup-$(date +\%Y\%m\%d).sql.gz
```

### Database Restore

```bash
# Stop the application
docker-compose down

# Remove old data volume
docker volume rm nigeria-security-system_postgres_data

# Start only the database
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Restore from backup
gunzip -c backups/backup-20250121-020000.sql.gz | \
  docker-compose exec -T postgres psql -U postgres nigeria_security

# Start all services
docker-compose up -d
```

### Disaster Recovery Plan

1. **Data**: Regular PostgreSQL backups (daily recommended)
2. **Configuration**: `.env` file backed up securely
3. **Code**: Version controlled in Git
4. **Recovery Time Objective (RTO)**: < 1 hour
5. **Recovery Point Objective (RPO)**: < 24 hours

## Troubleshooting

### Common Issues

#### 1. Frontend Can't Connect to Backend

**Symptoms**: "Network error: Unable to reach the server"

**Solutions**:
```bash
# Check if backend is running
docker-compose ps backend

# Check backend logs for errors
docker-compose logs backend

# Verify CORS settings in .env
# Ensure ALLOWED_ORIGINS includes your frontend URL

# Restart backend
docker-compose restart backend
```

#### 2. Database Connection Errors

**Symptoms**: "Could not connect to database"

**Solutions**:
```bash
# Check if postgres is healthy
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Verify credentials in .env match DATABASE_URL

# Wait for database to be fully ready
docker-compose restart postgres
sleep 30
docker-compose restart backend
```

#### 3. Mapbox Map Not Loading

**Symptoms**: Blank map or "Unauthorized" error

**Solutions**:
- Verify `VITE_MAPBOX_TOKEN` is set correctly in `.env`
- Check token is valid at https://account.mapbox.com/
- Ensure domain is authorized in Mapbox account settings
- Rebuild frontend: `docker-compose up -d --build frontend`

#### 4. Port Already in Use

**Symptoms**: "Bind for 0.0.0.0:80 failed: port is already allocated"

**Solutions**:
```bash
# Find process using port 80
sudo lsof -i :80  # Linux/Mac
netstat -ano | findstr :80  # Windows

# Either stop the conflicting service or change ports in docker-compose.yml
ports:
  - "8080:80"  # Use port 8080 instead
```

#### 5. Out of Memory Errors

**Symptoms**: Services keep restarting, "Killed" in logs

**Solutions**:
```bash
# Check available memory
free -h  # Linux
docker stats  # Check container memory usage

# Increase Docker memory limits in docker-compose.yml
services:
  backend:
    mem_limit: 2g
    mem_reservation: 1g
```

### Debug Mode

Enable debug logging:

```bash
# Edit .env
DEBUG=true

# Restart services
docker-compose restart backend

# View detailed logs
docker-compose logs -f backend
```

### Getting Help

If issues persist:

1. Check service logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Check health status: `docker-compose ps`
4. Review backend API errors: http://localhost:8000/docs
5. Open an issue on the project repository

## Maintenance Schedule

### Daily
- Monitor application logs
- Check service health status

### Weekly
- Review error logs for patterns
- Check disk space usage
- Verify backup completion

### Monthly
- Update Docker images
- Review and rotate credentials
- Test backup restoration
- Security audit and updates

### Quarterly
- Performance optimization review
- Database optimization (VACUUM, REINDEX)
- Disaster recovery drill
- Dependency updates

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Mapbox GL JS Documentation](https://docs.mapbox.com/mapbox-gl-js/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## Support

For technical support or questions:
- Create an issue in the project repository
- Refer to the main README.md for development setup
- Check API documentation at `/docs` endpoint
