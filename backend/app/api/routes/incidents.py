"""
Incident API endpoints for creating and querying security incidents
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from geoalchemy2.functions import ST_Distance, ST_DWithin
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import csv
import io

from app.database import get_db
from app.models.incident import Incident, IncidentType, SeverityLevel
from app.models.user import User
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    IncidentListResponse,
    NearbyIncidentsQuery,
    IncidentGeoJSON,
    IncidentStats
)
from app.utils.spatial_utils import (
    create_point_geometry,
    validate_nigerian_coordinates,
    extract_coordinates_from_geometry,
    haversine_distance
)
from app.utils.geocoding import reverse_geocode, extract_state_from_coordinates
from app.utils.sanitization import sanitize_text_field, sanitize_list_field, validate_no_null_bytes
from app.services.verification import calculate_verification_score
from app.api.dependencies.auth import get_current_user, require_admin
from app.utils.audit import log_admin_action

router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new security incident report

    This endpoint accepts incident reports with GPS coordinates, validates them,
    calculates a verification score, and stores them in the database.

    - **incident_type**: Type of security incident
    - **severity**: Severity level (low, moderate, high, critical)
    - **location**: GeoJSON Point with [longitude, latitude]
    - **description**: Detailed description of the incident
    - **timestamp**: When the incident occurred
    - **casualties**: Optional casualty information
    - **reporter_phone**: Optional phone number of reporter
    """
    # Extract coordinates
    longitude, latitude = incident_data.location.coordinates

    # Validate coordinates are within Nigeria
    if not validate_nigerian_coordinates(longitude, latitude):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coordinates ({latitude}, {longitude}) are outside Nigerian boundaries"
        )

    # Sanitize text inputs to prevent XSS attacks
    try:
        sanitized_description = sanitize_text_field(incident_data.description)
        validate_no_null_bytes(sanitized_description)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Sanitize optional list fields
    sanitized_media_urls = sanitize_list_field(incident_data.media_urls) if incident_data.media_urls else []
    sanitized_tags = sanitize_list_field(incident_data.tags) if incident_data.tags else []

    # Get or create user/reporter
    reporter = None
    reporter_trust_score = 0.5  # Default for anonymous

    if incident_data.reporter_phone and not incident_data.is_anonymous:
        reporter = db.query(User).filter(
            User.phone_number == incident_data.reporter_phone
        ).first()

        if not reporter:
            # Create new user
            reporter = User(
                phone_number=incident_data.reporter_phone,
                trust_score=0.5
            )
            db.add(reporter)
            db.flush()
        else:
            reporter.reports_submitted += 1

        reporter_trust_score = reporter.trust_score

    # Perform reverse geocoding to get location name and state
    location_info = await reverse_geocode(latitude, longitude)

    if location_info:
        location_name = location_info.get("location_name", "Unknown Location")
        state = location_info.get("state")
        lga = location_info.get("lga")
    else:
        # Fallback if geocoding fails
        location_name = f"{latitude:.4f}, {longitude:.4f}"
        state = extract_state_from_coordinates(latitude, longitude)
        lga = None

    # Calculate verification score (use sanitized description)
    verification_score = calculate_verification_score(
        incident_type=incident_data.incident_type,
        latitude=latitude,
        longitude=longitude,
        timestamp=incident_data.timestamp,
        reporter_trust_score=reporter_trust_score,
        description=sanitized_description,
        db=db
    )

    # Auto-verify if score is high enough
    from app.config import get_settings
    settings = get_settings()
    auto_verified = verification_score >= settings.AUTO_VERIFY_THRESHOLD

    # Create PostGIS geometry
    point_geometry = create_point_geometry(longitude, latitude)

    # Convert casualties to JSONB format
    casualties_data = None
    if incident_data.casualties:
        casualties_data = incident_data.casualties.model_dump()

    # Create incident (use sanitized values for security)
    incident = Incident(
        incident_type=incident_data.incident_type,
        severity=incident_data.severity,
        location=point_geometry,
        location_name=location_name,
        state=state,
        lga=lga,
        description=sanitized_description,  # XSS protection
        timestamp=incident_data.timestamp,
        casualties=casualties_data,
        verified=auto_verified,
        verification_score=verification_score,
        reporter_id=reporter.id if reporter else None,
        reporter_phone=incident_data.reporter_phone if incident_data.is_anonymous else None,
        is_anonymous=incident_data.is_anonymous,
        media_urls=sanitized_media_urls,  # XSS protection
        tags=sanitized_tags  # XSS protection
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Note: latitude and longitude are automatically extracted from geometry via @property methods

    return incident


@router.get("/recent", response_model=List[IncidentResponse])
async def get_recent_incidents(
    limit: int = Query(10, ge=1, le=50),
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get most recent incidents

    - **limit**: Maximum number of incidents to return (default: 10, max: 50)
    - **severity**: Filter by severity level (optional)
    """
    query = db.query(Incident)

    if severity:
        try:
            severity_level = SeverityLevel(severity)
            query = query.filter(Incident.severity == severity_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity level: {severity}"
            )

    incidents = query.order_by(desc(Incident.created_at)).limit(limit).all()

    return incidents


# ==================== Incident Verification ====================

@router.post("/{incident_id}/verify", dependencies=[Depends(require_admin)])
async def verify_incident(
    incident_id: UUID,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify an incident (admin only)

    Marks an incident as verified by an administrator.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

    if incident.verified:
        return {"message": "Incident already verified", "incident_id": str(incident_id)}

    # Update incident
    incident.verified = True
    incident.verified_by = current_user.id

    if notes:
        incident.verification_notes = notes

    db.commit()
    db.refresh(incident)

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="verify_incident",
        resource_type="incident",
        resource_id=str(incident_id),
        changes={"notes": notes} if notes else None,
        status="success"
    )

    return {
        "message": "Incident verified successfully",
        "incident_id": str(incident_id),
        "verified_by": current_user.email
    }


@router.post("/{incident_id}/unverify", dependencies=[Depends(require_admin)])
async def unverify_incident(
    incident_id: UUID,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unverify an incident (admin only)

    Removes verification status from an incident.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

    if not incident.verified:
        return {"message": "Incident not verified", "incident_id": str(incident_id)}

    # Update incident
    incident.verified = False
    incident.verified_by = None

    if reason:
        incident.verification_notes = f"Unverified: {reason}"

    db.commit()
    db.refresh(incident)

    # Log action
    log_admin_action(
        db=db,
        user_id=current_user.id,
        action="unverify_incident",
        resource_type="incident",
        resource_id=str(incident_id),
        changes={"reason": reason} if reason else None,
        status="success"
    )

    return {
        "message": "Incident unverified successfully",
        "incident_id": str(incident_id),
        "unverified_by": current_user.email
    }


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific incident by ID
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )

    return incident


@router.get("", response_model=IncidentListResponse)
@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    incident_type: Optional[IncidentType] = None,
    severity: Optional[SeverityLevel] = None,
    state: Optional[str] = None,
    verified_only: bool = False,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    List incidents with filtering and pagination

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
    - **incident_type**: Filter by incident type
    - **severity**: Filter by severity level
    - **state**: Filter by Nigerian state
    - **verified_only**: Only return verified incidents
    - **days**: Number of days to look back (default: 30)
    """
    # Build query
    query = db.query(Incident)

    # Apply filters
    time_threshold = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Incident.timestamp >= time_threshold)

    if incident_type:
        query = query.filter(Incident.incident_type == incident_type)

    if severity:
        query = query.filter(Incident.severity == severity)

    if state:
        query = query.filter(Incident.state == state)

    if verified_only:
        query = query.filter(Incident.verified == True)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    query = query.order_by(desc(Incident.timestamp))
    offset = (page - 1) * page_size
    incidents = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "incidents": incidents
    }


@router.get("/nearby/search", response_model=List[IncidentResponse])
async def search_nearby_incidents(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50.0, gt=0, le=500),
    days: int = Query(7, gt=0, le=365),
    incident_types: Optional[str] = Query(None),
    severities: Optional[str] = Query(None),
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Find incidents near a specific location

    - **latitude**: Center latitude
    - **longitude**: Center longitude
    - **radius_km**: Search radius in kilometers (default: 50, max: 500)
    - **days**: Number of days to look back (default: 7)
    - **incident_types**: Comma-separated incident types
    - **severities**: Comma-separated severity levels
    - **verified_only**: Only return verified incidents
    """
    # Validate coordinates
    if not validate_nigerian_coordinates(longitude, latitude):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coordinates are outside Nigerian boundaries"
        )

    # Create point geometry
    point = create_point_geometry(longitude, latitude)

    # Convert radius to degrees (approximate)
    from app.utils.spatial_utils import kilometers_to_degrees
    radius_degrees = kilometers_to_degrees(radius_km, latitude)

    # Build query with spatial filter
    query = db.query(Incident).filter(
        ST_DWithin(Incident.location, point, radius_degrees)
    )

    # Apply time filter
    time_threshold = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Incident.timestamp >= time_threshold)

    # Parse and apply incident type filter
    if incident_types:
        types_list = [IncidentType(t.strip()) for t in incident_types.split(",")]
        query = query.filter(Incident.incident_type.in_(types_list))

    # Parse and apply severity filter
    if severities:
        severity_list = [SeverityLevel(s.strip()) for s in severities.split(",")]
        query = query.filter(Incident.severity.in_(severity_list))

    if verified_only:
        query = query.filter(Incident.verified == True)

    # Execute query
    incidents = query.order_by(desc(Incident.timestamp)).limit(200).all()

    # Add coordinates and distance to each incident
    for incident in incidents:
        coords = extract_coordinates_from_geometry(incident.location)
        if coords:
            inc_lon, inc_lat = coords
            incident.longitude = inc_lon
            incident.latitude = inc_lat
            # Calculate actual distance
            incident.distance_km = haversine_distance(longitude, latitude, inc_lon, inc_lat)

    # Sort by distance
    incidents.sort(key=lambda x: getattr(x, 'distance_km', 0))

    return incidents


@router.get("/geojson/all", response_model=dict)
async def get_incidents_geojson(
    days: int = Query(30, ge=1, le=365),
    incident_type: Optional[IncidentType] = None,
    severity: Optional[SeverityLevel] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all incidents as GeoJSON FeatureCollection for map visualization

    - **days**: Number of days to look back (default: 30)
    - **incident_type**: Filter by incident type
    - **severity**: Filter by severity level
    - **verified_only**: Only return verified incidents
    """
    # Build query
    query = db.query(Incident)

    time_threshold = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Incident.timestamp >= time_threshold)

    if incident_type:
        query = query.filter(Incident.incident_type == incident_type)

    if severity:
        query = query.filter(Incident.severity == severity)

    if verified_only:
        query = query.filter(Incident.verified == True)

    incidents = query.limit(1000).all()  # Limit to prevent huge responses

    # Convert to GeoJSON
    features = []
    for incident in incidents:
        coords = extract_coordinates_from_geometry(incident.location)
        if coords:
            lon, lat = coords
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": str(incident.id),
                    "incident_type": incident.incident_type.value,
                    "severity": incident.severity.value,
                    "severity_score": incident.severity_score,
                    "description": incident.description,
                    "location_name": incident.location_name,
                    "state": incident.state,
                    "verified": incident.verified,
                    "verification_score": incident.verification_score,
                    "casualties": incident.casualties,
                    "timestamp": incident.timestamp.isoformat() if incident.timestamp else None
                }
            }
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/stats/summary", response_model=IncidentStats)
async def get_incident_statistics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get statistical summary of incidents with comparison to previous period

    - **days**: Number of days to look back (default: 30)
    """
    time_threshold = datetime.utcnow() - timedelta(days=days)
    previous_threshold = time_threshold - timedelta(days=days)

    # Total incidents - current period
    total = db.query(Incident).filter(
        Incident.timestamp >= time_threshold
    ).count()

    # Total incidents - previous period (for comparison)
    previous_total = db.query(Incident).filter(
        and_(
            Incident.timestamp >= previous_threshold,
            Incident.timestamp < time_threshold
        )
    ).count()

    # By type
    by_type = db.query(
        Incident.incident_type,
        func.count(Incident.id)
    ).filter(
        Incident.timestamp >= time_threshold
    ).group_by(Incident.incident_type).all()

    # By severity
    by_severity = db.query(
        Incident.severity,
        func.count(Incident.id)
    ).filter(
        Incident.timestamp >= time_threshold
    ).group_by(Incident.severity).all()

    # By state
    by_state = db.query(
        Incident.state,
        func.count(Incident.id)
    ).filter(
        and_(
            Incident.timestamp >= time_threshold,
            Incident.state.isnot(None)
        )
    ).group_by(Incident.state).order_by(desc(func.count(Incident.id))).limit(10).all()

    # Verified vs unverified - current period
    verified_count = db.query(Incident).filter(
        and_(
            Incident.timestamp >= time_threshold,
            Incident.verified == True
        )
    ).count()

    # Verified - previous period (for comparison)
    previous_verified = db.query(Incident).filter(
        and_(
            Incident.timestamp >= previous_threshold,
            Incident.timestamp < time_threshold,
            Incident.verified == True
        )
    ).count()

    # Calculate total casualties - current period
    incidents_with_casualties = db.query(Incident).filter(
        and_(
            Incident.timestamp >= time_threshold,
            Incident.casualties.isnot(None)
        )
    ).all()

    total_killed = sum(inc.casualties.get('killed', 0) for inc in incidents_with_casualties if inc.casualties)
    total_injured = sum(inc.casualties.get('injured', 0) for inc in incidents_with_casualties if inc.casualties)
    total_missing = sum(inc.casualties.get('missing', 0) for inc in incidents_with_casualties if inc.casualties)
    current_casualties_total = total_killed + total_injured + total_missing

    # Calculate total casualties - previous period (for comparison)
    previous_incidents_with_casualties = db.query(Incident).filter(
        and_(
            Incident.timestamp >= previous_threshold,
            Incident.timestamp < time_threshold,
            Incident.casualties.isnot(None)
        )
    ).all()

    previous_killed = sum(inc.casualties.get('killed', 0) for inc in previous_incidents_with_casualties if inc.casualties)
    previous_injured = sum(inc.casualties.get('injured', 0) for inc in previous_incidents_with_casualties if inc.casualties)
    previous_missing = sum(inc.casualties.get('missing', 0) for inc in previous_incidents_with_casualties if inc.casualties)
    previous_casualties_total = previous_killed + previous_injured + previous_missing

    # Calculate percentage changes
    def calculate_change(current: int, previous: int) -> float:
        """Calculate percentage change, handling division by zero"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100

    total_incidents_change = calculate_change(total, previous_total)
    verified_count_change = calculate_change(verified_count, previous_verified)
    casualties_change = calculate_change(current_casualties_total, previous_casualties_total)

    return {
        "total_incidents": total,
        "by_type": {str(t[0].value): t[1] for t in by_type},
        "by_severity": {str(s[0].value): s[1] for s in by_severity},
        "by_state": {s[0]: s[1] for s in by_state if s[0]},
        "verified_count": verified_count,
        "unverified_count": total - verified_count,
        "casualties_total": {
            "killed": total_killed,
            "injured": total_injured,
            "missing": total_missing
        },
        "time_range_start": time_threshold,
        "time_range_end": datetime.utcnow(),
        "total_incidents_change": round(total_incidents_change, 1),
        "verified_count_change": round(verified_count_change, 1),
        "casualties_change": round(casualties_change, 1),
        "previous_period_total": previous_total
    }


@router.get("/stats/timeseries")
async def get_incident_timeseries(
    days: int = Query(30, ge=1, le=365),
    interval: str = Query("day", regex="^(hour|day|week)$"),
    db: Session = Depends(get_db)
):
    """
    Get time series data of incidents over time

    - **days**: Number of days to look back (default: 30)
    - **interval**: Aggregation interval: hour, day, or week (default: day)
    """
    time_threshold = datetime.utcnow() - timedelta(days=days)

    # Determine date trunc format based on interval
    if interval == "hour":
        trunc_format = "hour"
    elif interval == "week":
        trunc_format = "week"
    else:  # day
        trunc_format = "day"

    # Query incidents grouped by time interval
    timeseries_data = db.query(
        func.date_trunc(trunc_format, Incident.timestamp).label('time_bucket'),
        func.count(Incident.id).label('total'),
        func.count(func.nullif(Incident.severity == SeverityLevel.CRITICAL, False)).label('critical'),
        func.count(func.nullif(Incident.severity == SeverityLevel.HIGH, False)).label('high'),
        func.count(func.nullif(Incident.severity == SeverityLevel.MODERATE, False)).label('moderate'),
        func.count(func.nullif(Incident.severity == SeverityLevel.LOW, False)).label('low')
    ).filter(
        Incident.timestamp >= time_threshold
    ).group_by('time_bucket').order_by('time_bucket').all()

    # Format response
    series = []
    for row in timeseries_data:
        series.append({
            "date": row.time_bucket.isoformat(),
            "total": row.total,
            "critical": row.critical,
            "high": row.high,
            "moderate": row.moderate,
            "low": row.low
        })

    return {
        "interval": interval,
        "time_range_start": time_threshold.isoformat(),
        "time_range_end": datetime.utcnow().isoformat(),
        "series": series
    }


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing incident (admin only in production)

    - **incident_id**: UUID of the incident to update
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )

    # Update fields
    update_data = incident_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "casualties" and value:
            setattr(incident, field, value.model_dump())
        else:
            setattr(incident, field, value)

    db.commit()
    db.refresh(incident)

    # Add coordinates
    coords = extract_coordinates_from_geometry(incident.location)
    if coords:
        incident.longitude, incident.latitude = coords

    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an incident (admin only in production)

    - **incident_id**: UUID of the incident to delete
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )

    db.delete(incident)
    db.commit()

    return None


@router.get("/export/csv")
async def export_incidents_csv(
    days: int = Query(30, ge=1, le=365),
    incident_type: Optional[str] = None,
    severity: Optional[str] = None,
    state: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Export incidents to CSV format

    - **days**: Number of days to look back (default: 30)
    - **incident_type**: Filter by incident type (optional)
    - **severity**: Filter by severity level (optional)
    - **state**: Filter by Nigerian state (optional)
    - **verified_only**: Only include verified incidents (default: false)
    """
    time_threshold = datetime.utcnow() - timedelta(days=days)

    # Build query with filters
    query = db.query(Incident).filter(Incident.timestamp >= time_threshold)

    if incident_type:
        try:
            inc_type = IncidentType(incident_type)
            query = query.filter(Incident.incident_type == inc_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid incident type: {incident_type}"
            )

    if severity:
        try:
            severity_level = SeverityLevel(severity)
            query = query.filter(Incident.severity == severity_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity level: {severity}"
            )

    if state:
        query = query.filter(Incident.state == state)

    if verified_only:
        query = query.filter(Incident.verified == True)

    # Order by timestamp descending
    incidents = query.order_by(desc(Incident.timestamp)).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'ID',
        'Type',
        'Severity',
        'Description',
        'State',
        'LGA',
        'Location Name',
        'Latitude',
        'Longitude',
        'Timestamp',
        'Verified',
        'Verification Score',
        'Killed',
        'Injured',
        'Missing',
        'Tags',
        'Created At'
    ])

    # Write data rows
    for incident in incidents:
        coords = extract_coordinates_from_geometry(incident.location)
        latitude, longitude = coords if coords else (None, None)

        casualties = incident.casualties or {}
        killed = casualties.get('killed', 0)
        injured = casualties.get('injured', 0)
        missing = casualties.get('missing', 0)

        tags = ','.join(incident.tags) if incident.tags else ''

        writer.writerow([
            str(incident.id),
            incident.incident_type.value,
            incident.severity.value,
            incident.description,
            incident.state or '',
            incident.lga or '',
            incident.location_name or '',
            latitude,
            longitude,
            incident.timestamp.isoformat(),
            incident.verified,
            incident.verification_score,
            killed,
            injured,
            missing,
            tags,
            incident.created_at.isoformat() if incident.created_at else ''
        ])

    # Prepare response
    output.seek(0)
    filename = f"incidents_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
