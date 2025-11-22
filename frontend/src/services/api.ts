/**
 * API Service Layer
 * Handles all HTTP requests to the backend API
 */

import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  Incident,
  IncidentCreate,
  IncidentUpdate,
  IncidentListResponse,
  IncidentStats,
  IncidentGeoJSON,
  IncidentListParams,
  NearbySearchParams,
} from '@/types/incident';
import { toast } from 'sonner';

// API Base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Create Axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    // Future: Add authentication token here
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as { detail?: string };

      switch (status) {
        case 400:
          toast.error(`Bad Request: ${data.detail || 'Invalid input'}`);
          break;
        case 404:
          toast.error('Resource not found');
          break;
        case 422:
          toast.error('Validation error: Please check your input');
          break;
        case 500:
          toast.error('Server error: Please try again later');
          break;
        default:
          toast.error(`Error: ${data.detail || 'Something went wrong'}`);
      }
    } else if (error.request) {
      // Request made but no response received
      toast.error('Network error: Unable to reach the server');
    } else {
      // Something else happened
      toast.error('An unexpected error occurred');
    }

    return Promise.reject(error);
  }
);

/**
 * Incident Service
 * All API methods related to incidents
 */
export const incidentService = {
  /**
   * Get paginated list of incidents
   */
  async list(params?: IncidentListParams): Promise<IncidentListResponse> {
    const response = await apiClient.get<IncidentListResponse>('/incidents', {
      params: {
        page: params?.page || 1,
        page_size: params?.page_size || 20,
        incident_type: params?.incident_type,
        severity: params?.severity,
        state: params?.state,
        verified_only: params?.verified_only,
        days: params?.days,
      },
    });
    return response.data;
  },

  /**
   * Get single incident by ID
   */
  async getById(id: string): Promise<Incident> {
    const response = await apiClient.get<Incident>(`/incidents/${id}`);
    return response.data;
  },

  /**
   * Create new incident
   */
  async create(data: IncidentCreate): Promise<Incident> {
    const response = await apiClient.post<Incident>('/incidents', data);
    toast.success('Incident reported successfully');
    return response.data;
  },

  /**
   * Update existing incident
   */
  async update(id: string, data: IncidentUpdate): Promise<Incident> {
    const response = await apiClient.put<Incident>(`/incidents/${id}`, data);
    toast.success('Incident updated successfully');
    return response.data;
  },

  /**
   * Delete incident
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/incidents/${id}`);
    toast.success('Incident deleted successfully');
  },

  /**
   * Search for nearby incidents
   */
  async nearby(params: NearbySearchParams): Promise<Incident[]> {
    const response = await apiClient.get<Incident[]>('/incidents/nearby/search', {
      params: {
        latitude: params.latitude,
        longitude: params.longitude,
        radius_km: params.radius_km || 50,
        days: params.days || 30,
        incident_types: params.incident_types,
        severities: params.severities,
        verified_only: params.verified_only,
      },
    });
    return response.data;
  },

  /**
   * Get incident statistics
   */
  async stats(days: number = 30): Promise<IncidentStats> {
    const response = await apiClient.get<IncidentStats>('/incidents/stats/summary', {
      params: { days },
    });
    return response.data;
  },

  /**
   * Get incidents as GeoJSON for map display
   */
  async geojson(params?: {
    days?: number;
    incident_type?: string;
    severity?: string;
    state?: string;
    verified_only?: boolean;
  }): Promise<IncidentGeoJSON> {
    const response = await apiClient.get<IncidentGeoJSON>('/incidents/geojson/all', {
      params: {
        days: params?.days || 30,
        incident_type: params?.incident_type,
        severity: params?.severity,
        state: params?.state,
        verified_only: params?.verified_only,
      },
    });
    return response.data;
  },

  /**
   * Get time series data for trend analysis
   */
  async timeseries(days: number = 30, interval: 'hour' | 'day' | 'week' = 'day') {
    const response = await apiClient.get('/incidents/stats/timeseries', {
      params: { days, interval },
    });
    return response.data;
  },

  /**
   * Get recent incidents
   */
  async recent(limit: number = 10, severity?: string): Promise<Incident[]> {
    const response = await apiClient.get<Incident[]>('/incidents/recent', {
      params: { limit, severity },
    });
    return response.data;
  },
};

/**
 * Health check endpoint
 */
export const healthService = {
  async check(): Promise<{ status: string; timestamp: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

/**
 * Export the configured axios instance for custom requests
 */
export default apiClient;
