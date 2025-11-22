/**
 * Mapbox GL JS Configuration
 * Nigeria-specific map settings and utilities
 */

import mapboxgl from 'mapbox-gl';
import type { LngLatBoundsLike, LngLatLike } from 'mapbox-gl';
import { SeverityLevel } from '@/types/incident';

// Initialize Mapbox token from environment variable
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

if (MAPBOX_TOKEN && !MAPBOX_TOKEN.includes('placeholder')) {
  mapboxgl.accessToken = MAPBOX_TOKEN;
}

// Nigeria geographic bounds [west, south, east, north]
export const NIGERIA_BOUNDS: LngLatBoundsLike = [
  [2.668, 4.277], // Southwest corner [longitude, latitude]
  [14.678, 13.892], // Northeast corner
];

// Nigeria center coordinates [longitude, latitude]
export const NIGERIA_CENTER: LngLatLike = [8.6753, 9.082];

// Default map configuration
export const DEFAULT_MAP_CONFIG = {
  style: 'mapbox://styles/mapbox/streets-v12',
  center: NIGERIA_CENTER,
  zoom: 6,
  maxBounds: NIGERIA_BOUNDS,
  minZoom: 5,
  maxZoom: 18,
};

// Map style options
export const MAP_STYLES = {
  streets: 'mapbox://styles/mapbox/streets-v12',
  satellite: 'mapbox://styles/mapbox/satellite-streets-v12',
  outdoors: 'mapbox://styles/mapbox/outdoors-v12',
  light: 'mapbox://styles/mapbox/light-v11',
  dark: 'mapbox://styles/mapbox/dark-v11',
};

/**
 * Get marker color based on severity level
 */
export const getSeverityColor = (severity: SeverityLevel): string => {
  switch (severity) {
    case SeverityLevel.CRITICAL:
      return '#DC2626'; // Red
    case SeverityLevel.HIGH:
      return '#EA580C'; // Orange
    case SeverityLevel.MODERATE:
      return '#F59E0B'; // Yellow
    case SeverityLevel.LOW:
      return '#16A34A'; // Green
    default:
      return '#6B7280'; // Gray
  }
};

/**
 * Get marker size based on severity level
 */
export const getSeveritySize = (severity: SeverityLevel): number => {
  switch (severity) {
    case SeverityLevel.CRITICAL:
      return 16;
    case SeverityLevel.HIGH:
      return 14;
    case SeverityLevel.MODERATE:
      return 12;
    case SeverityLevel.LOW:
      return 10;
    default:
      return 10;
  }
};

/**
 * Create a custom marker element
 */
export const createMarkerElement = (
  severity: SeverityLevel,
  verified: boolean
): HTMLDivElement => {
  const el = document.createElement('div');
  el.className = 'custom-marker';
  el.style.width = `${getSeveritySize(severity)}px`;
  el.style.height = `${getSeveritySize(severity)}px`;
  el.style.backgroundColor = getSeverityColor(severity);
  el.style.borderRadius = '50%';
  el.style.border = verified ? '2px solid white' : '2px dashed white';
  el.style.cursor = 'pointer';
  el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
  el.style.transition = 'transform 0.2s';

  // Hover effect
  el.addEventListener('mouseenter', () => {
    el.style.transform = 'scale(1.2)';
  });
  el.addEventListener('mouseleave', () => {
    el.style.transform = 'scale(1)';
  });

  return el;
};

/**
 * Format coordinates for display
 */
export const formatCoordinates = (lng: number, lat: number): string => {
  return `${lat.toFixed(6)}°N, ${lng.toFixed(6)}°E`;
};

/**
 * Calculate distance between two points in kilometers
 */
export const calculateDistance = (
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Convert degrees to radians
 */
const toRadians = (degrees: number): number => {
  return degrees * (Math.PI / 180);
};

/**
 * Get user's current location
 */
export const getCurrentLocation = (): Promise<GeolocationPosition> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by your browser'));
    } else {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      });
    }
  });
};

/**
 * Check if coordinates are within Nigeria bounds
 */
export const isInNigeria = (lng: number, lat: number): boolean => {
  const [sw, ne] = NIGERIA_BOUNDS as [[number, number], [number, number]];
  return lng >= sw[0] && lng <= ne[0] && lat >= sw[1] && lat <= ne[1];
};

/**
 * Nigerian major cities for quick navigation
 */
export const NIGERIAN_CITIES = [
  { name: 'Lagos', coordinates: [3.3792, 6.5244] as LngLatLike },
  { name: 'Abuja', coordinates: [7.4951, 9.0765] as LngLatLike },
  { name: 'Kano', coordinates: [8.5167, 12.0022] as LngLatLike },
  { name: 'Ibadan', coordinates: [3.8964, 7.3775] as LngLatLike },
  { name: 'Port Harcourt', coordinates: [7.0498, 4.8156] as LngLatLike },
  { name: 'Kaduna', coordinates: [7.4388, 10.5105] as LngLatLike },
  { name: 'Benin City', coordinates: [5.6258, 6.3382] as LngLatLike },
  { name: 'Maiduguri', coordinates: [13.1571, 11.8333] as LngLatLike },
  { name: 'Jos', coordinates: [8.8921, 9.9285] as LngLatLike },
  { name: 'Enugu', coordinates: [7.4951, 6.4403] as LngLatLike },
];

export default mapboxgl;
