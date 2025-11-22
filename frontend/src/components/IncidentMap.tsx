/**
 * IncidentMap Component
 * Displays a Mapbox map with incident markers
 */

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { useQuery } from '@tanstack/react-query';
import { incidentService } from '@/services/api';
import {
  DEFAULT_MAP_CONFIG,
  createMarkerElement,
  getCurrentLocation,
  NIGERIA_CENTER,
  formatCoordinates,
} from '@/utils/mapConfig';
import {
  Incident,
  IncidentType,
  SeverityLevel,
  incidentTypeLabels,
  severityLabels,
} from '@/types/incident';
import { toast } from 'sonner';
import 'mapbox-gl/dist/mapbox-gl.css';

interface IncidentMapProps {
  days?: number;
  incidentType?: IncidentType;
  severity?: SeverityLevel;
  state?: string;
  verifiedOnly?: boolean;
  onIncidentClick?: (incident: Incident) => void;
}

export default function IncidentMap({
  days = 30,
  incidentType,
  severity,
  state,
  verifiedOnly = false,
  onIncidentClick,
}: IncidentMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);

  // Fetch incidents as GeoJSON
  const { data: geojson, isLoading, error } = useQuery({
    queryKey: ['incidents-geojson', days, incidentType, severity, state, verifiedOnly],
    queryFn: () =>
      incidentService.geojson({
        days,
        incident_type: incidentType,
        severity,
        state,
        verified_only: verifiedOnly,
      }),
    refetchInterval: 60000, // Refetch every minute
  });

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Check if Mapbox token is configured
    const token = import.meta.env.VITE_MAPBOX_TOKEN;
    if (!token || token.includes('placeholder')) {
      toast.error('Mapbox token not configured. Please add your token to .env file');
      return;
    }

    // Create map instance
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      ...DEFAULT_MAP_CONFIG,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add fullscreen control
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    // Map loaded event
    map.current.on('load', () => {
      setMapLoaded(true);
    });

    // Cleanup on unmount
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update markers when data changes
  useEffect(() => {
    if (!map.current || !mapLoaded || !geojson) return;

    // Clear existing markers
    markers.current.forEach((marker) => marker.remove());
    markers.current = [];

    // Add markers for each incident
    geojson.features.forEach((feature) => {
      const { geometry, properties } = feature;
      const [lng, lat] = geometry.coordinates;

      // Create marker element
      const el = createMarkerElement(
        properties.severity as SeverityLevel,
        properties.verified
      );

      // Create popup content
      const popupContent = `
        <div class="p-3 min-w-[250px]">
          <div class="flex items-start justify-between mb-2">
            <h3 class="font-semibold text-sm">
              ${incidentTypeLabels[properties.incident_type as IncidentType]}
            </h3>
            <span class="severity-badge severity-${properties.severity}">
              ${severityLabels[properties.severity as SeverityLevel]}
            </span>
          </div>

          <p class="text-xs text-gray-600 mb-2 line-clamp-2">
            ${properties.description}
          </p>

          <div class="space-y-1 text-xs text-gray-500">
            <div class="flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <span>${properties.location_name || formatCoordinates(lng, lat)}</span>
            </div>

            ${properties.state ? `
              <div class="flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>
                </svg>
                <span>${properties.state}</span>
              </div>
            ` : ''}

            <div class="flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>${new Date(properties.timestamp).toLocaleDateString()}</span>
            </div>

            ${properties.casualties && (properties.casualties.killed > 0 || properties.casualties.injured > 0) ? `
              <div class="flex items-center gap-1 text-red-600 font-medium">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <span>
                  ${properties.casualties.killed > 0 ? `${properties.casualties.killed} killed` : ''}
                  ${properties.casualties.killed > 0 && properties.casualties.injured > 0 ? ', ' : ''}
                  ${properties.casualties.injured > 0 ? `${properties.casualties.injured} injured` : ''}
                </span>
              </div>
            ` : ''}

            <div class="flex items-center gap-1 ${properties.verified ? 'text-green-600' : 'text-yellow-600'}">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${properties.verified ? `
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                ` : `
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                `}
              </svg>
              <span>${properties.verified ? 'Verified' : 'Unverified'} (${Math.round(properties.verification_score * 100)}%)</span>
            </div>
          </div>

          <button
            onclick="window.viewIncident('${properties.id}')"
            class="mt-3 w-full px-3 py-1.5 bg-nigeria-green text-white text-xs font-medium rounded hover:bg-green-700 transition-colors"
          >
            View Details
          </button>
        </div>
      `;

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: 25,
        closeButton: true,
        closeOnClick: false,
        maxWidth: '300px',
      }).setHTML(popupContent);

      // Create marker
      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(map.current!);

      // Handle marker click
      el.addEventListener('click', () => {
        if (onIncidentClick) {
          // Fetch full incident data
          const incident: Incident = {
            id: properties.id,
            incident_type: properties.incident_type as IncidentType,
            severity: properties.severity as SeverityLevel,
            severity_score: properties.severity_score,
            location: geometry,
            location_name: properties.location_name,
            state: properties.state,
            description: properties.description,
            timestamp: properties.timestamp,
            casualties: properties.casualties,
            verified: properties.verified,
            verification_score: properties.verification_score,
            latitude: lat,
            longitude: lng,
          };
          onIncidentClick(incident);
        }
      });

      markers.current.push(marker);
    });

    // Fit map to show all markers
    if (geojson.features.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      geojson.features.forEach((feature) => {
        bounds.extend(feature.geometry.coordinates as [number, number]);
      });
      map.current.fitBounds(bounds, { padding: 50, maxZoom: 10 });
    }
  }, [geojson, mapLoaded, onIncidentClick]);

  // Handle user location
  const handleFindMe = async () => {
    try {
      const position = await getCurrentLocation();
      const { longitude, latitude } = position.coords;

      setUserLocation([longitude, latitude]);

      // Add user location marker
      if (map.current) {
        const el = document.createElement('div');
        el.className = 'w-4 h-4 bg-blue-500 border-2 border-white rounded-full shadow-lg';

        new mapboxgl.Marker({ element: el })
          .setLngLat([longitude, latitude])
          .setPopup(
            new mapboxgl.Popup({ offset: 15 })
              .setHTML('<div class="p-2 text-xs font-medium">Your Location</div>')
          )
          .addTo(map.current);

        map.current.flyTo({
          center: [longitude, latitude],
          zoom: 10,
          duration: 2000,
        });
      }

      toast.success('Location found!');
    } catch (error) {
      toast.error('Unable to get your location. Please enable location services.');
    }
  };

  // Global function for viewing incident details
  useEffect(() => {
    (window as any).viewIncident = (id: string) => {
      window.location.href = `/incidents/${id}`;
    };
  }, []);

  return (
    <div className="relative w-full h-full">
      {/* Map container */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nigeria-green mx-auto mb-4"></div>
            <p className="text-gray-600">Loading incidents...</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-50 border border-red-200 text-red-800 px-4 py-2 rounded-lg shadow-lg z-10">
          <p className="text-sm">Failed to load incidents. Please try again.</p>
        </div>
      )}

      {/* Find Me button */}
      <button
        onClick={handleFindMe}
        className="absolute bottom-24 right-4 bg-white hover:bg-gray-50 text-gray-700 p-3 rounded-lg shadow-lg transition-colors z-10 border border-gray-200"
        title="Find my location"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>

      {/* Incident count badge */}
      {geojson && (
        <div className="absolute top-4 left-4 bg-white px-4 py-2 rounded-lg shadow-lg z-10 border border-gray-200">
          <p className="text-sm font-medium text-gray-700">
            {geojson.features.length} incident{geojson.features.length !== 1 ? 's' : ''} in last {days} days
          </p>
        </div>
      )}
    </div>
  );
}
