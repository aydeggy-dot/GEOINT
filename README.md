# Nigeria Security Early Warning System

A real-time security incident mapping and early warning system for Nigeria that leverages geospatial intelligence to help communities, humanitarian organizations, and security agencies respond to security threats.

## Features

### Current Implementation (MVP)
- **Incident Reporting**: Crowdsourced incident reporting with GPS coordinates
- **Spatial Validation**: Validates coordinates are within Nigerian boundaries
- **Automated Verification**: Multi-factor verification scoring based on:
  - Spatial plausibility
  - Temporal consistency
  - Reporter credibility
  - Cross-verification with nearby reports
  - Description quality
- **Geospatial Queries**: Find incidents near any location with customizable radius
- **GeoJSON Export**: Export incidents for map visualization
- **Statistics Dashboard**: Real-time statistics by type, severity, state, and casualties
- **PostGIS Integration**: Advanced spatial database for efficient geospatial operations

### Planned Features
- Predictive risk modeling using machine learning
- Automated early warning alerts via SMS and push notifications
- Heat map and hotspot analysis
- Safe route navigation
- Satellite imagery integration
- Offline functionality for low-connectivity areas

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 with PostGIS 3.3
- **ORM**: SQLAlchemy with GeoAlchemy2
- **Geospatial**: Shapely, GeoPy
- **Caching**: Redis

### Frontend (Coming Soon)
- **Framework**: React with Mapbox GL JS
- **UI**: Material-UI or Tailwind CSS
- **State Management**: React Context API

## Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd nigeria-security-system
```

2. **Start the services**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL with PostGIS on port 5432
- Redis on port 6379
- FastAPI backend on port 8000

3. **Verify the installation**
```bash
curl http://localhost:8000/health
```

4. **Access the API documentation**
Open your browser to: http://localhost:8000/docs

### Local Development Setup

1. **Create a virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start PostgreSQL and Redis** (if not using Docker)
```bash
docker-compose up -d postgres redis
```

5. **Run database migrations**
```bash
# The database is auto-initialized on first run
# To manually initialize:
python -c "from app.database import init_db, create_spatial_indexes; init_db(); create_spatial_indexes()"
```

6. **Run the development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

### Create an Incident Report

```bash
curl -X POST "http://localhost:8000/api/v1/incidents/" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "armed_attack",
    "severity": "high",
    "location": {
      "type": "Point",
      "coordinates": [7.4905, 9.0765]
    },
    "description": "Armed men attacked village at dawn, multiple casualties reported",
    "timestamp": "2025-11-20T06:30:00Z",
    "casualties": {
      "killed": 5,
      "injured": 12,
      "missing": 0
    },
    "reporter_phone": "+234XXXXXXXXXX"
  }'
```

### Search Nearby Incidents

```bash
curl "http://localhost:8000/api/v1/incidents/nearby/search?latitude=9.0765&longitude=7.4905&radius_km=50&days=7"
```

### Get Incidents as GeoJSON

```bash
curl "http://localhost:8000/api/v1/incidents/geojson/all?days=30&verified_only=true"
```

### Get Statistics

```bash
curl "http://localhost:8000/api/v1/incidents/stats/summary?days=30"
```

## Database Schema

### Incidents Table
- `id`: UUID primary key
- `incident_type`: Type of security incident (enum)
- `severity`: Severity level (low, moderate, high, critical)
- `location`: PostGIS POINT geometry (WGS84)
- `location_name`: Human-readable location
- `state`: Nigerian state
- `lga`: Local Government Area
- `description`: Detailed description
- `verified`: Auto-verification status
- `verification_score`: 0-1 confidence score
- `casualties`: JSONB with killed/injured/missing counts
- `timestamp`: When incident occurred
- `reporter_id`: Foreign key to users table
- `media_urls`: Array of photo/video URLs
- `tags`: Array of tags for categorization

### Users Table
- `id`: UUID primary key
- `phone_number`: Contact number (hashed in production)
- `trust_score`: 0-1 credibility score
- `reports_submitted/verified/rejected`: Tracking metrics
- `location`: Last known location for alerts
- `receive_alerts`: Alert preferences

## Verification System

Incidents are automatically scored based on five factors:

1. **Spatial Plausibility (20%)**: Is the location plausible for this incident type?
   - Insurgent attacks more likely in Borno/Yobe
   - Banditry more common in Zamfara/Katsina
   - Farmer-herder clashes in Middle Belt

2. **Temporal Plausibility (15%)**: Is the timing reasonable?
   - Future timestamps = 0 score
   - Recent reports (< 24h) score highest

3. **Reporter Credibility (30%)**: Historical accuracy of reporter
   - New reporters start at 0.5
   - Score increases with verified reports
   - Decreases with rejected reports

4. **Cross-Verification (25%)**: Are there similar nearby reports?
   - Multiple reports within 10km and 6 hours = higher confidence

5. **Description Quality (10%)**: Is the description detailed?
   - Word count and specific details increase score

**Auto-Verification**: Incidents scoring ≥0.8 are automatically verified.
**Manual Review**: Incidents scoring 0.5-0.8 require admin review.
**Low Confidence**: Incidents <0.5 are flagged as suspicious.

## Incident Types

- `armed_attack`: Armed attacks on communities
- `kidnapping`: Abduction incidents
- `banditry`: Bandit activities
- `insurgent_attack`: Boko Haram/ISWAP attacks
- `farmer_herder_clash`: Farmer-herder conflicts
- `robbery`: Armed robbery
- `communal_clash`: Inter-communal violence
- `cattle_rustling`: Livestock theft
- `bomb_blast`: Explosions/IEDs
- `shooting`: Shooting incidents
- `other`: Other security incidents

## Nigerian States Coverage

All 36 states plus FCT:
- Northeast: Borno, Yobe, Adamawa, Bauchi, Gombe, Taraba
- Northwest: Zamfara, Katsina, Sokoto, Kebbi, Kaduna, Kano, Jigawa
- North Central: Plateau, Benue, Nasarawa, Niger, Kogi, Kwara, FCT
- Southwest: Lagos, Ogun, Oyo, Osun, Ondo, Ekiti
- Southeast: Enugu, Ebonyi, Anambra, Imo, Abia
- South-South: Rivers, Bayelsa, Delta, Edo, Akwa Ibom, Cross River

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest backend/tests/test_incidents.py
```

## Project Structure

```
nigeria-security-system/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Helper functions
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Test files
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/                # React frontend (coming soon)
├── data/                    # GeoJSON boundaries and sample data
├── scripts/                 # Utility scripts
└── docker-compose.yml       # Docker orchestration
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key
- `ALLOWED_ORIGINS`: CORS allowed origins
- `AUTO_VERIFY_THRESHOLD`: Score for auto-verification (0.8)
- `IMMEDIATE_ZONE_KM`: Alert radius for critical incidents (5km)
- `MAPBOX_ACCESS_TOKEN`: For map visualization
- `AFRICASTALKING_API_KEY`: For SMS alerts

## Security Considerations

### Production Deployment

1. **Change default credentials** in docker-compose.yml
2. **Set strong SECRET_KEY** in .env
3. **Hash phone numbers** before storage
4. **Enable HTTPS** with SSL/TLS certificates
5. **Implement authentication** (JWT tokens)
6. **Rate limiting** to prevent abuse
7. **Input sanitization** to prevent injection attacks
8. **Encrypt sensitive data** at rest

### Privacy

- Anonymous reporting supported
- Phone numbers can be hashed/encrypted
- Location data stored only for active incidents
- GDPR/privacy compliance ready

## Performance Optimization

- Spatial indexes on all geometry columns
- Connection pooling (10 connections, 20 max overflow)
- Redis caching for frequently accessed data
- Query result pagination
- GeoJSON simplification for large polygons

## Roadmap

### Phase 2: Analytics (Weeks 3-4)
- [ ] Hotspot analysis (Getis-Ord Gi*)
- [ ] Heat map generation (KDE)
- [ ] Temporal trend analysis
- [ ] State-level comparisons

### Phase 3: Predictions (Weeks 5-6)
- [ ] Feature engineering for ML model
- [ ] Train Random Forest/XGBoost
- [ ] Risk score predictions (7-day forecast)
- [ ] Accuracy tracking and model updates

### Phase 4: Alerts (Weeks 7-8)
- [ ] Alert generation system
- [ ] SMS integration (Africa's Talking)
- [ ] Push notifications
- [ ] User notification preferences
- [ ] Alert history and logs

### Phase 5: Advanced Features (Weeks 9-10)
- [ ] Safe route calculation
- [ ] Evacuation planning tools
- [ ] Admin verification dashboard
- [ ] Satellite imagery analysis
- [ ] Export/reporting (PDF, CSV)

### Future Enhancements
- Mobile app (React Native/Flutter)
- Offline mode with sync
- Multi-language support (Hausa, Yoruba, Igbo)
- Integration with emergency services
- Community leader dashboards
- WhatsApp bot for reporting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Contact

[Your contact information]

## Acknowledgments

- Built for humanitarian and security purposes
- Designed with input from Nigerian security experts
- GeoJSON boundaries from Humanitarian Data Exchange
- OpenStreetMap for geocoding services

## Disclaimer

This system is for informational and humanitarian purposes. Always verify critical information through official channels. The developers are not responsible for decisions made based on this data.
