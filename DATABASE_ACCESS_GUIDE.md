# Database Access Guide
## Nigeria Security Early Warning System

---

## Database Configuration

### Default Credentials (Docker Setup)

```
Host:     localhost
Port:     5432
Database: nigeria_security
Username: postgres
Password: postgres
```

**Connection String:**
```
postgresql://postgres:postgres@localhost:5432/nigeria_security
```

---

## Option 1: Access via Docker (Recommended)

### Start the Database

```bash
cd C:\DEV\GEOINT\nigeria-security-system

# Start PostgreSQL with PostGIS
docker-compose up -d postgres

# Verify it's running
docker-compose ps
```

### Access PostgreSQL Shell (psql)

```bash
# Method 1: Direct docker exec
docker exec -it nigeria-security-postgres psql -U postgres -d nigeria_security

# Method 2: Via docker-compose
docker-compose exec postgres psql -U postgres -d nigeria_security
```

Once connected, you'll see:
```
nigeria_security=#
```

### Basic SQL Commands

```sql
-- List all tables
\dt

-- Describe incidents table
\d incidents

-- Count incidents
SELECT COUNT(*) FROM incidents;

-- View recent incidents
SELECT id, incident_type, severity, location_name, state, timestamp
FROM incidents
ORDER BY timestamp DESC
LIMIT 10;

-- Get incidents by state
SELECT state, COUNT(*) as count
FROM incidents
GROUP BY state
ORDER BY count DESC;

-- Get incidents by type
SELECT incident_type, COUNT(*) as count
FROM incidents
GROUP BY incident_type
ORDER BY count DESC;

-- View PostGIS version
SELECT PostGIS_version();

-- Exit
\q
```

---

## Option 2: Using pgAdmin (GUI Tool)

### Install pgAdmin
Download from: https://www.pgadmin.org/download/

### Configure Connection

1. **Open pgAdmin**
2. **Right-click "Servers"** → **Create** → **Server**
3. **General Tab:**
   - Name: `Nigeria Security DB`

4. **Connection Tab:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `nigeria_security`
   - Username: `postgres`
   - Password: `postgres`

5. **Click Save**

### Browse Data

Navigate to:
```
Servers → Nigeria Security DB → Databases → nigeria_security → Schemas → public → Tables
```

Right-click any table → **View/Edit Data** → **All Rows**

---

## Option 3: Using DBeaver (Free Universal Database Tool)

### Install DBeaver
Download from: https://dbeaver.io/download/

### Configure Connection

1. **Click "New Database Connection"**
2. **Select "PostgreSQL"**
3. **Enter Details:**
   ```
   Host: localhost
   Port: 5432
   Database: nigeria_security
   Username: postgres
   Password: postgres
   ```
4. **Test Connection**
5. **Click Finish**

### View Spatial Data

DBeaver has built-in support for PostGIS:
- Click on any row with geometry
- Click the "Geometry Viewer" tab
- View incident locations on a map

---

## Option 4: Using Python Script

### Create Database Viewer Script

Save as `view_database.py`:

```python
import psycopg2
from datetime import datetime

# Connection details
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="nigeria_security",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()

# Get table statistics
print("\n" + "="*70)
print("DATABASE STATISTICS")
print("="*70 + "\n")

# Count tables
cursor.execute("""
    SELECT COUNT(*) FROM incidents
""")
incident_count = cursor.fetchone()[0]
print(f"Total Incidents: {incident_count}")

cursor.execute("""
    SELECT COUNT(*) FROM users
""")
user_count = cursor.fetchone()[0]
print(f"Total Users: {user_count}")

# Recent incidents
print("\n" + "="*70)
print("RECENT INCIDENTS")
print("="*70 + "\n")

cursor.execute("""
    SELECT
        incident_type,
        severity,
        location_name,
        state,
        verified,
        timestamp
    FROM incidents
    ORDER BY timestamp DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    inc_type, severity, location, state, verified, timestamp = row
    status = "✓" if verified else "✗"
    print(f"{status} [{severity:8}] {inc_type:20} | {location:30} | {state}")

# Incidents by state
print("\n" + "="*70)
print("INCIDENTS BY STATE (Top 10)")
print("="*70 + "\n")

cursor.execute("""
    SELECT state, COUNT(*) as count
    FROM incidents
    WHERE state IS NOT NULL
    GROUP BY state
    ORDER BY count DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    state, count = row
    bar = "█" * min(count // 2, 50)
    print(f"{state:30} {count:4} {bar}")

# Close connection
cursor.close()
conn.close()

print("\n" + "="*70 + "\n")
```

### Run the Script

```bash
# Install psycopg2 (if not already installed)
pip install psycopg2-binary

# Run the viewer
python view_database.py
```

---

## Option 5: Using DataGrip (JetBrains - Commercial)

### Install DataGrip
Download from: https://www.jetbrains.com/datagrip/

### Configure Connection

1. **Click "+"** → **Data Source** → **PostgreSQL**
2. **Enter Connection Details:**
   ```
   Host: localhost
   Port: 5432
   Database: nigeria_security
   User: postgres
   Password: postgres
   ```
3. **Download Drivers** (if prompted)
4. **Test Connection**
5. **Click OK**

### Features
- SQL autocompletion
- Visual query builder
- ER diagrams
- Data export (CSV, JSON, Excel)

---

## Database Schema Overview

### Tables

```sql
-- 1. INCIDENTS TABLE
CREATE TABLE incidents (
    id UUID PRIMARY KEY,
    incident_type VARCHAR(50),        -- armed_attack, kidnapping, etc.
    severity VARCHAR(20),             -- low, moderate, high, critical
    location GEOMETRY(POINT, 4326),   -- PostGIS point (lon, lat)
    location_name VARCHAR(255),       -- "Jos, Plateau"
    state VARCHAR(100),               -- "Plateau"
    lga VARCHAR(100),                 -- Local Government Area
    description TEXT,
    verified BOOLEAN,
    verification_score FLOAT,
    reporter_id UUID,
    casualties JSONB,                 -- {"killed": 5, "injured": 12}
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    media_urls TEXT[],
    tags TEXT[]
);

-- 2. USERS TABLE
CREATE TABLE users (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,
    email VARCHAR(255),
    trust_score FLOAT,                -- 0-1
    reports_submitted INTEGER,
    reports_verified INTEGER,
    reports_rejected INTEGER,
    location GEOMETRY(POINT, 4326),
    receive_alerts BOOLEAN,
    alert_radius_km FLOAT,
    is_active BOOLEAN,
    is_admin BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
);

-- 3. ALERTS TABLE
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    incident_id UUID,
    alert_type VARCHAR(20),           -- critical, high, medium, low
    message TEXT,
    target_area GEOMETRY(POLYGON, 4326),
    radius_km FLOAT,
    status VARCHAR(20),
    recipients_count INTEGER,
    delivery_status JSONB,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);

-- 4. PREDICTIONS TABLE
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    location GEOMETRY(POINT, 4326),
    grid_cell_id VARCHAR(50),
    state VARCHAR(100),
    risk_score FLOAT,                 -- 0-100
    confidence FLOAT,                 -- 0-1
    prediction_date DATE,
    factors JSONB,
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
);
```

---

## Useful SQL Queries

### 1. View All Incidents with Coordinates

```sql
SELECT
    id,
    incident_type,
    severity,
    location_name,
    state,
    ST_X(location) as longitude,
    ST_Y(location) as latitude,
    verified,
    timestamp
FROM incidents
ORDER BY timestamp DESC;
```

### 2. Find Incidents Near a Location (within 50km)

```sql
SELECT
    incident_type,
    location_name,
    ST_Distance(
        location::geography,
        ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 4326)::geography
    ) / 1000 as distance_km
FROM incidents
WHERE ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(7.4905, 9.0765), 4326)::geography,
    50000  -- 50km in meters
)
ORDER BY distance_km;
```

### 3. Incidents by Month

```sql
SELECT
    DATE_TRUNC('month', timestamp) as month,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE verified = true) as verified_count
FROM incidents
GROUP BY month
ORDER BY month DESC;
```

### 4. Casualty Statistics

```sql
SELECT
    SUM((casualties->>'killed')::int) as total_killed,
    SUM((casualties->>'injured')::int) as total_injured,
    SUM((casualties->>'missing')::int) as total_missing
FROM incidents
WHERE casualties IS NOT NULL;
```

### 5. Top Reporters by Trust Score

```sql
SELECT
    phone_number,
    trust_score,
    reports_submitted,
    reports_verified,
    reports_rejected,
    ROUND(reports_verified::numeric / NULLIF(reports_submitted, 0) * 100, 2) as verification_rate
FROM users
WHERE reports_submitted > 0
ORDER BY trust_score DESC
LIMIT 10;
```

### 6. Incidents Heat Map Data (Export for Mapbox)

```sql
SELECT
    json_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(location)::json,
        'properties', json_build_object(
            'incident_type', incident_type,
            'severity', severity,
            'location_name', location_name,
            'verified', verified,
            'timestamp', timestamp
        )
    ) as geojson_feature
FROM incidents
WHERE timestamp > NOW() - INTERVAL '30 days';
```

---

## Export Data

### Export to CSV

```sql
-- From psql
\copy (SELECT * FROM incidents) TO 'C:/incidents.csv' CSV HEADER;

-- Or use DBeaver/pgAdmin GUI export features
```

### Export to JSON

```python
import psycopg2
import json

conn = psycopg2.connect(
    host="localhost",
    database="nigeria_security",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()
cursor.execute("SELECT row_to_json(incidents) FROM incidents")

incidents = [row[0] for row in cursor.fetchall()]

with open('incidents.json', 'w') as f:
    json.dump(incidents, f, indent=2, default=str)

print(f"Exported {len(incidents)} incidents to incidents.json")
```

---

## Database Backup & Restore

### Backup Database

```bash
# Using docker
docker exec -t nigeria-security-postgres pg_dump -U postgres nigeria_security > backup.sql

# Or from host (if PostgreSQL client installed)
pg_dump -h localhost -p 5432 -U postgres nigeria_security > backup.sql
```

### Restore Database

```bash
# Using docker
cat backup.sql | docker exec -i nigeria-security-postgres psql -U postgres -d nigeria_security

# Or from host
psql -h localhost -p 5432 -U postgres -d nigeria_security < backup.sql
```

---

## Troubleshooting

### Can't Connect to Database

1. **Check if Docker is running:**
```bash
docker-compose ps
```

2. **Check if PostgreSQL container is running:**
```bash
docker ps | grep postgres
```

3. **View PostgreSQL logs:**
```bash
docker-compose logs postgres
```

4. **Restart PostgreSQL:**
```bash
docker-compose restart postgres
```

### Password Authentication Failed

Make sure you're using the correct credentials from `docker-compose.yml`:
- Username: `postgres`
- Password: `postgres`

### Port Already in Use

If port 5432 is already used:
1. Stop other PostgreSQL instances
2. Or change port in `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use 5433 on host
```

Then connect to `localhost:5433`

---

## Security Notes

### For Production

⚠️ **IMPORTANT:** Change default credentials before deployment!

1. **Update `docker-compose.yml`:**
```yaml
environment:
  POSTGRES_USER: secure_username
  POSTGRES_PASSWORD: VeryStrongPassword123!
```

2. **Update `.env`:**
```
DATABASE_URL=postgresql://secure_username:VeryStrongPassword123!@postgres:5432/nigeria_security
```

3. **Restrict access:**
   - Don't expose port 5432 to the internet
   - Use firewall rules
   - Set up SSL/TLS for connections
   - Use connection pooling with PgBouncer

---

## Quick Reference

### Connection URLs

**Local Development:**
```
postgresql://postgres:postgres@localhost:5432/nigeria_security
```

**With Docker Compose (from another container):**
```
postgresql://postgres:postgres@postgres:5432/nigeria_security
```

**SQLAlchemy Format:**
```python
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/nigeria_security"
```

**Django Format:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'nigeria_security',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## Summary

### Easiest Methods:

1. **Quick View (Terminal):**
   ```bash
   docker exec -it nigeria-security-postgres psql -U postgres -d nigeria_security
   ```

2. **GUI Tool (Best for Exploration):**
   - Install pgAdmin or DBeaver
   - Connect with credentials above
   - Browse tables visually

3. **Python Script:**
   - Use the `view_database.py` script provided
   - Great for automated reports

### Connection Details:
```
Host:     localhost
Port:     5432
Database: nigeria_security
Username: postgres
Password: postgres
```

**Ready to access your database!** 🎉
