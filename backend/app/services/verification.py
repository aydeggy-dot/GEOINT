"""
Incident verification service for calculating verification scores
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from geoalchemy2.functions import ST_Distance, ST_DWithin
from app.models.incident import Incident, IncidentType
from app.models.user import User
from app.utils.spatial_utils import validate_nigerian_coordinates, create_point_geometry
from app.config import CONFLICT_ZONES


def calculate_verification_score(
    incident_type: IncidentType,
    latitude: float,
    longitude: float,
    timestamp: datetime,
    reporter_trust_score: float,
    description: str,
    db: Session
) -> float:
    """
    Calculate verification score for an incident based on multiple factors

    Args:
        incident_type: Type of incident
        latitude: Incident latitude
        longitude: Incident longitude
        timestamp: When incident occurred
        reporter_trust_score: Trust score of the reporter
        description: Incident description
        db: Database session

    Returns:
        Verification score between 0.0 and 1.0
    """
    score = 0.0
    weight_sum = 0.0

    # Factor 1: Spatial Plausibility (20% weight)
    spatial_score = check_spatial_plausibility(latitude, longitude, incident_type)
    score += spatial_score * 0.20
    weight_sum += 0.20

    # Factor 2: Temporal Plausibility (15% weight)
    temporal_score = check_temporal_plausibility(timestamp, incident_type)
    score += temporal_score * 0.15
    weight_sum += 0.15

    # Factor 3: Reporter Credibility (30% weight)
    score += reporter_trust_score * 0.30
    weight_sum += 0.30

    # Factor 4: Cross-verification with nearby reports (25% weight)
    cross_verify_score = check_cross_verification(
        latitude, longitude, timestamp, incident_type, db
    )
    score += cross_verify_score * 0.25
    weight_sum += 0.25

    # Factor 5: Description Quality (10% weight)
    description_score = check_description_quality(description)
    score += description_score * 0.10
    weight_sum += 0.10

    # Normalize score
    final_score = score / weight_sum if weight_sum > 0 else 0.5

    return max(0.0, min(1.0, final_score))


def check_spatial_plausibility(latitude: float, longitude: float, incident_type: IncidentType) -> float:
    """
    Check if the location is plausible for the incident type

    Args:
        latitude: Incident latitude
        longitude: Incident longitude
        incident_type: Type of incident

    Returns:
        Score between 0.0 and 1.0
    """
    # Base check: Is it within Nigeria?
    if not validate_nigerian_coordinates(longitude, latitude):
        return 0.0

    # Check if incident type matches known conflict zones
    # For example, insurgent attacks are more likely in Borno/Yobe
    # This is a simplified version - in production, use actual state polygon lookup

    score = 0.7  # Default moderate plausibility

    # High-risk incident types in known conflict zones get higher scores
    if incident_type in [IncidentType.INSURGENT_ATTACK, IncidentType.BOMB_BLAST]:
        # Check if in northeast (Borno, Yobe, Adamawa region)
        if 10.5 <= latitude <= 13.9 and 11.0 <= longitude <= 14.5:
            score = 0.9  # Very plausible
        else:
            score = 0.6  # Less common but possible

    elif incident_type in [IncidentType.BANDITRY, IncidentType.KIDNAPPING, IncidentType.CATTLE_RUSTLING]:
        # Check if in northwest (Zamfara, Katsina, Sokoto region)
        if 11.0 <= latitude <= 13.5 and 4.0 <= longitude <= 9.0:
            score = 0.9
        else:
            score = 0.7

    elif incident_type == IncidentType.FARMER_HERDER_CLASH:
        # Check if in middle belt (Plateau, Benue, Nasarawa region)
        if 6.5 <= latitude <= 10.0 and 7.0 <= longitude <= 10.0:
            score = 0.9
        else:
            score = 0.7

    return score


def check_temporal_plausibility(timestamp: datetime, incident_type: IncidentType) -> float:
    """
    Check if the timestamp is plausible

    Args:
        timestamp: Incident timestamp
        incident_type: Type of incident

    Returns:
        Score between 0.0 and 1.0
    """
    from datetime import timezone
    now = datetime.now(timezone.utc)

    # Can't be in the future
    if timestamp > now:
        return 0.0

    # Too old (more than 7 days) is suspicious for immediate reporting
    days_old = (now - timestamp).days
    if days_old > 7:
        return 0.4
    elif days_old > 3:
        return 0.6
    elif days_old > 1:
        return 0.8
    else:
        return 1.0  # Recent reports are most credible


def check_cross_verification(
    latitude: float,
    longitude: float,
    timestamp: datetime,
    incident_type: IncidentType,
    db: Session
) -> float:
    """
    Check if other reports exist nearby around the same time

    Args:
        latitude: Incident latitude
        longitude: Incident longitude
        timestamp: Incident timestamp
        incident_type: Type of incident
        db: Database session

    Returns:
        Score between 0.0 and 1.0
    """
    # Look for similar incidents within 10km and 6 hours
    point = create_point_geometry(longitude, latitude)
    time_window_start = timestamp - timedelta(hours=6)
    time_window_end = timestamp + timedelta(hours=6)

    # Query for nearby incidents
    nearby_count = db.query(Incident).filter(
        and_(
            ST_DWithin(
                Incident.location,
                point,
                0.09  # ~10km in degrees
            ),
            Incident.timestamp.between(time_window_start, time_window_end),
            Incident.incident_type == incident_type
        )
    ).count()

    # More nearby reports = higher confidence
    if nearby_count >= 3:
        return 1.0
    elif nearby_count == 2:
        return 0.9
    elif nearby_count == 1:
        return 0.7
    else:
        return 0.5  # No corroboration, but not necessarily false


def check_description_quality(description: str) -> float:
    """
    Check the quality and detail of the description

    Args:
        description: Incident description

    Returns:
        Score between 0.0 and 1.0
    """
    if not description:
        return 0.0

    description = description.strip()
    word_count = len(description.split())

    # Keyword indicators of detailed reports
    detail_keywords = [
        'armed', 'men', 'attacked', 'village', 'town', 'killed', 'injured',
        'gunmen', 'soldiers', 'police', 'morning', 'evening', 'night',
        'road', 'market', 'church', 'mosque', 'school', 'fled', 'casualties'
    ]

    keyword_matches = sum(1 for keyword in detail_keywords if keyword.lower() in description.lower())

    # Score based on length and detail
    score = 0.5  # Base score

    if word_count >= 20:
        score += 0.2
    elif word_count >= 10:
        score += 0.1

    if keyword_matches >= 3:
        score += 0.3
    elif keyword_matches >= 1:
        score += 0.15

    return min(1.0, score)


async def update_reporter_trust_after_verification(
    reporter_id: str,
    was_verified: bool,
    db: Session
) -> None:
    """
    Update reporter's trust score after incident verification

    Args:
        reporter_id: UUID of the reporter
        was_verified: Whether the incident was verified or rejected
        db: Database session
    """
    user = db.query(User).filter(User.id == reporter_id).first()

    if not user:
        return

    # Update counts
    if was_verified:
        user.reports_verified += 1
    else:
        user.reports_rejected += 1

    # Recalculate trust score
    user.update_trust_score()

    db.commit()
