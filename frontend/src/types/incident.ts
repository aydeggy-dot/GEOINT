/**
 * TypeScript types for incidents matching backend API models
 */

// Incident type enum matching backend
export enum IncidentType {
  ARMED_ATTACK = 'armed_attack',
  INSURGENT_ATTACK = 'insurgent_attack',
  KIDNAPPING = 'kidnapping',
  BANDITRY = 'banditry',
  FARMER_HERDER_CLASH = 'farmer_herder_clash',
  CATTLE_RUSTLING = 'cattle_rustling',
  BOMB_BLAST = 'bomb_blast',
  ROBBERY = 'robbery',
  COMMUNAL_CLASH = 'communal_clash',
}

// Severity level enum
export enum SeverityLevel {
  LOW = 'low',
  MODERATE = 'moderate',
  HIGH = 'high',
  CRITICAL = 'critical',
}

// GeoJSON Point geometry
export interface PointGeometry {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

// Casualties information
export interface Casualties {
  killed: number;
  injured: number;
  missing: number;
}

// Main Incident interface
export interface Incident {
  id: string;
  incident_type: IncidentType;
  severity: SeverityLevel;
  severity_score?: number;
  location: PointGeometry;
  location_name?: string;
  state?: string;
  lga?: string;
  description: string;
  timestamp: string; // ISO 8601 datetime string
  casualties?: Casualties;
  verified: boolean;
  verification_score: number;
  reporter_id?: string;
  reporter_phone?: string;
  is_anonymous?: boolean;
  media_urls?: string[];
  tags?: string[];
  created_at?: string;
  updated_at?: string;
  // Computed properties from backend
  latitude?: number;
  longitude?: number;
  distance_km?: number; // For nearby search results
}

// Incident creation payload
export interface IncidentCreate {
  incident_type: IncidentType;
  severity: SeverityLevel;
  location: PointGeometry;
  description: string;
  timestamp: string;
  casualties?: Casualties;
  reporter_phone?: string;
  is_anonymous?: boolean;
  media_urls?: string[];
  tags?: string[];
}

// Incident update payload
export interface IncidentUpdate {
  severity?: SeverityLevel;
  description?: string;
  verified?: boolean;
  casualties?: Casualties;
}

// Paginated list response
export interface IncidentListResponse {
  total: number;
  page: number;
  page_size: number;
  incidents: Incident[];
}

// Statistics response
export interface IncidentStats {
  total_incidents: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_state: Record<string, number>;
  verified_count: number;
  unverified_count: number;
  casualties_total: {
    killed: number;
    injured: number;
    missing: number;
  };
  time_range_start: string;
  time_range_end: string;
  // Comparison metrics
  total_incidents_change?: number;
  verified_count_change?: number;
  casualties_change?: number;
  previous_period_total?: number;
}

// GeoJSON Feature for map display
export interface IncidentFeature {
  type: 'Feature';
  geometry: PointGeometry;
  properties: {
    id: string;
    incident_type: string;
    severity: string;
    severity_score: number;
    description: string;
    location_name: string;
    state: string;
    verified: boolean;
    verification_score: number;
    casualties: Casualties | null;
    timestamp: string;
  };
}

// GeoJSON FeatureCollection
export interface IncidentGeoJSON {
  type: 'FeatureCollection';
  features: IncidentFeature[];
}

// Query parameters for listing incidents
export interface IncidentListParams {
  page?: number;
  page_size?: number;
  incident_type?: IncidentType;
  severity?: SeverityLevel;
  state?: string;
  verified_only?: boolean;
  days?: number;
}

// Query parameters for nearby search
export interface NearbySearchParams {
  latitude: number;
  longitude: number;
  radius_km?: number;
  days?: number;
  incident_types?: string; // Comma-separated
  severities?: string; // Comma-separated
  verified_only?: boolean;
}

// Helper type for incident type labels
export const incidentTypeLabels: Record<IncidentType, string> = {
  [IncidentType.ARMED_ATTACK]: 'Armed Attack',
  [IncidentType.INSURGENT_ATTACK]: 'Insurgent Attack',
  [IncidentType.KIDNAPPING]: 'Kidnapping',
  [IncidentType.BANDITRY]: 'Banditry',
  [IncidentType.FARMER_HERDER_CLASH]: 'Farmer-Herder Clash',
  [IncidentType.CATTLE_RUSTLING]: 'Cattle Rustling',
  [IncidentType.BOMB_BLAST]: 'Bomb Blast',
  [IncidentType.ROBBERY]: 'Robbery',
  [IncidentType.COMMUNAL_CLASH]: 'Communal Clash',
};

// Helper type for severity labels
export const severityLabels: Record<SeverityLevel, string> = {
  [SeverityLevel.LOW]: 'Low',
  [SeverityLevel.MODERATE]: 'Moderate',
  [SeverityLevel.HIGH]: 'High',
  [SeverityLevel.CRITICAL]: 'Critical',
};

// Helper type for severity colors (Tailwind classes)
export const severityColors: Record<SeverityLevel, string> = {
  [SeverityLevel.LOW]: 'severity-low',
  [SeverityLevel.MODERATE]: 'severity-moderate',
  [SeverityLevel.HIGH]: 'severity-high',
  [SeverityLevel.CRITICAL]: 'severity-critical',
};

// Nigerian states list
export const NIGERIAN_STATES = [
  'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa',
  'Benue', 'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo',
  'Ekiti', 'Enugu', 'Gombe', 'Imo', 'Jigawa', 'Kaduna',
  'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos',
  'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo',
  'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara',
  'Federal Capital Territory',
] as const;

export type NigerianState = typeof NIGERIAN_STATES[number];
