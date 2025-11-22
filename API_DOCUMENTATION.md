# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently, the MVP does not require authentication. In production, use JWT tokens for protected endpoints.

---

## Endpoints

### Health Check

#### `GET /health`
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "nigeria-security-system"
}
```

---

## Incidents

### Create Incident

#### `POST /incidents/`
Create a new security incident report.

**Request Body:**
```json
{
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
  "reporter_phone": "+234XXXXXXXXXX",
  "is_anonymous": false,
  "media_urls": ["https://example.com/photo1.jpg"],
  "tags": ["urgent", "verified"]
}
```

**Parameters:**
- `incident_type` (required): One of:
  - `armed_attack`
  - `kidnapping`
  - `banditry`
  - `insurgent_attack`
  - `farmer_herder_clash`
  - `robbery`
  - `communal_clash`
  - `cattle_rustling`
  - `bomb_blast`
  - `shooting`
  - `other`

- `severity` (required): One of `low`, `moderate`, `high`, `critical`

- `location` (required): GeoJSON Point with `[longitude, latitude]`
  - Must be within Nigerian boundaries (4-14°N, 2.5-15°E)

- `description` (required): Minimum 10 characters

- `timestamp` (required): ISO 8601 datetime when incident occurred

- `casualties` (optional): Object with `killed`, `injured`, `missing` counts

- `reporter_phone` (optional): Reporter's phone number

- `is_anonymous` (optional): Boolean, default `false`

- `media_urls` (optional): Array of media URLs

- `tags` (optional): Array of tags

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "incident_type": "armed_attack",
  "severity": "high",
  "description": "Armed men attacked village...",
  "location_name": "Jos, Plateau State",
  "state": "Plateau",
  "lga": "Jos North",
  "verified": false,
  "verification_score": 0.72,
  "casualties": {
    "killed": 5,
    "injured": 12,
    "missing": 0
  },
  "timestamp": "2025-11-20T06:30:00Z",
  "created_at": "2025-11-20T10:15:30Z",
  "updated_at": "2025-11-20T10:15:30Z",
  "latitude": 9.0765,
  "longitude": 7.4905,
  "media_urls": ["https://example.com/photo1.jpg"],
  "tags": ["urgent", "verified"]
}
```

**Errors:**
- `400 Bad Request`: Coordinates outside Nigeria
- `422 Validation Error`: Invalid input data

---

### Get Incident

#### `GET /incidents/{incident_id}`
Retrieve a specific incident by ID.

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "incident_type": "armed_attack",
  ...
}
```

**Errors:**
- `404 Not Found`: Incident doesn't exist

---

### List Incidents

#### `GET /incidents/`
List incidents with filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number, default `1`
- `page_size` (optional): Items per page, default `50`, max `100`
- `incident_type` (optional): Filter by incident type
- `severity` (optional): Filter by severity level
- `state` (optional): Filter by Nigerian state
- `verified_only` (optional): Boolean, only return verified incidents
- `days` (optional): Number of days to look back, default `30`, max `365`

**Example:**
```
GET /incidents/?page=1&page_size=20&incident_type=kidnapping&severity=critical&state=Borno&verified_only=true&days=7
```

**Response (200 OK):**
```json
{
  "total": 125,
  "page": 1,
  "page_size": 20,
  "incidents": [
    {
      "id": "...",
      "incident_type": "kidnapping",
      ...
    }
  ]
}
```

---

### Search Nearby Incidents

#### `GET /incidents/nearby/search`
Find incidents within a radius of a location.

**Query Parameters:**
- `latitude` (required): Center latitude (-90 to 90)
- `longitude` (required): Center longitude (-180 to 180)
- `radius_km` (optional): Search radius in km, default `50`, max `500`
- `days` (optional): Days to look back, default `7`, max `365`
- `incident_types` (optional): Comma-separated types, e.g., `armed_attack,kidnapping`
- `severities` (optional): Comma-separated severities, e.g., `high,critical`
- `verified_only` (optional): Boolean

**Example:**
```
GET /incidents/nearby/search?latitude=9.0765&longitude=7.4905&radius_km=50&days=7&severities=high,critical
```

**Response (200 OK):**
```json
[
  {
    "id": "...",
    "incident_type": "armed_attack",
    "distance_km": 12.5,
    ...
  },
  {
    "id": "...",
    "incident_type": "kidnapping",
    "distance_km": 24.8,
    ...
  }
]
```

Results are sorted by distance (closest first).

**Errors:**
- `400 Bad Request`: Coordinates outside Nigeria

---

### Get GeoJSON

#### `GET /incidents/geojson/all`
Export incidents as GeoJSON FeatureCollection for map visualization.

**Query Parameters:**
- `days` (optional): Days to look back, default `30`, max `365`
- `incident_type` (optional): Filter by type
- `severity` (optional): Filter by severity
- `verified_only` (optional): Boolean

**Example:**
```
GET /incidents/geojson/all?days=30&severity=critical&verified_only=true
```

**Response (200 OK):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [7.4905, 9.0765]
      },
      "properties": {
        "id": "...",
        "incident_type": "armed_attack",
        "severity": "high",
        "severity_score": 75,
        "description": "...",
        "location_name": "Jos, Plateau",
        "state": "Plateau",
        "verified": true,
        "verification_score": 0.85,
        "casualties": {...},
        "timestamp": "2025-11-20T06:30:00Z"
      }
    }
  ]
}
```

Limited to 1000 incidents to prevent huge responses.

---

### Get Statistics

#### `GET /incidents/stats/summary`
Get statistical summary of incidents.

**Query Parameters:**
- `days` (optional): Days to look back, default `30`, max `365`

**Example:**
```
GET /incidents/stats/summary?days=30
```

**Response (200 OK):**
```json
{
  "total_incidents": 245,
  "by_type": {
    "armed_attack": 85,
    "kidnapping": 62,
    "banditry": 48,
    "insurgent_attack": 35,
    "farmer_herder_clash": 15
  },
  "by_severity": {
    "critical": 45,
    "high": 98,
    "moderate": 72,
    "low": 30
  },
  "by_state": {
    "Borno": 45,
    "Zamfara": 38,
    "Katsina": 32,
    "Plateau": 28,
    "Kaduna": 25,
    ...
  },
  "verified_count": 180,
  "unverified_count": 65,
  "casualties_total": {
    "killed": 456,
    "injured": 892,
    "missing": 123
  },
  "time_range_start": "2025-10-21T00:00:00Z",
  "time_range_end": "2025-11-20T15:30:00Z"
}
```

---

### Update Incident

#### `PATCH /incidents/{incident_id}`
Update an existing incident (admin only in production).

**Request Body (all fields optional):**
```json
{
  "incident_type": "kidnapping",
  "severity": "critical",
  "description": "Updated description with more details",
  "verified": true,
  "verification_notes": "Verified by admin after cross-checking",
  "casualties": {
    "killed": 8,
    "injured": 15,
    "missing": 3
  },
  "tags": ["verified", "admin-reviewed"]
}
```

**Response (200 OK):**
```json
{
  "id": "...",
  "incident_type": "kidnapping",
  ...
}
```

**Errors:**
- `404 Not Found`: Incident doesn't exist

---

### Delete Incident

#### `DELETE /incidents/{incident_id}`
Delete an incident (admin only in production).

**Response (204 No Content)**

**Errors:**
- `404 Not Found`: Incident doesn't exist

---

## Verification Scoring

Incidents are automatically scored on a 0-1 scale based on:

1. **Spatial Plausibility (20%)**: Location matches incident type patterns
   - Insurgent attacks in Borno/Yobe score higher
   - Banditry in Zamfara/Katsina scores higher
   - Farmer-herder clashes in Middle Belt score higher

2. **Temporal Plausibility (15%)**: Recent reports score higher
   - < 24 hours: 1.0
   - 1-3 days: 0.8
   - 3-7 days: 0.6
   - > 7 days: 0.4

3. **Reporter Credibility (30%)**: Based on historical accuracy
   - New reporters: 0.5
   - Increases with verified reports
   - Decreases with rejected reports

4. **Cross-Verification (25%)**: Multiple nearby reports increase score
   - 3+ reports within 10km & 6 hours: 1.0
   - 2 reports: 0.9
   - 1 report: 0.7
   - No corroboration: 0.5

5. **Description Quality (10%)**: Detailed descriptions score higher
   - Word count ≥ 20: +0.2
   - Specific keywords (armed, killed, village, etc.): +0.3

**Auto-Verification:**
- Score ≥ 0.8: Automatically verified
- Score 0.5-0.8: Requires manual review
- Score < 0.5: Flagged as suspicious

---

## Rate Limiting

In production, implement rate limiting:
- Anonymous reports: 10/hour per IP
- Authenticated users: 100/hour
- API queries: 1000/hour

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Coordinates (51.5074, 0.0) are outside Nigerian boundaries"
}
```

### 404 Not Found
```json
{
  "detail": "Incident 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "description"],
      "msg": "ensure this value has at least 10 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Data Formats

### Coordinates
Always use WGS84 (SRID 4326):
- Format: `[longitude, latitude]`
- Longitude: -180 to 180
- Latitude: -90 to 90

### Timestamps
Use ISO 8601 format with timezone:
- Example: `2025-11-20T06:30:00Z`
- UTC recommended

### Phone Numbers
Use E.164 format:
- Example: `+234XXXXXXXXXX`

---

## Nigerian States

Valid state names:
```
Abia, Adamawa, Akwa Ibom, Anambra, Bauchi, Bayelsa, Benue, Borno,
Cross River, Delta, Ebonyi, Edo, Ekiti, Enugu, Gombe, Imo, Jigawa,
Kaduna, Kano, Katsina, Kebbi, Kogi, Kwara, Lagos, Nasarawa, Niger,
Ogun, Ondo, Osun, Oyo, Plateau, Rivers, Sokoto, Taraba, Yobe,
Zamfara, Federal Capital Territory
```

---

## Best Practices

1. **Caching**: Cache GeoJSON and statistics for 5 minutes
2. **Pagination**: Always use pagination for list endpoints
3. **Filtering**: Combine filters to reduce data transfer
4. **Error Handling**: Handle 400, 404, 422, 500 errors gracefully
5. **Coordinates**: Validate coordinates client-side before submission
6. **Descriptions**: Encourage detailed, specific incident descriptions
7. **Timestamps**: Report incidents as soon as possible for higher verification scores

---

## Future Endpoints (Coming Soon)

- `GET /analytics/hotspots` - Hotspot analysis
- `GET /analytics/heatmap` - Heat map data
- `GET /predictions/risk` - Risk predictions
- `POST /alerts/generate` - Generate alerts
- `GET /routes/safe` - Safe route calculation
