import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { incidentService } from '@/services/api';
import { incidentTypeLabels, severityLabels } from '@/types/incident';
import { getCurrentLocation, formatCoordinates } from '@/utils/mapConfig';
import { toast } from 'sonner';

export default function NearbyPage() {
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [radiusKm, setRadiusKm] = useState(20);
  const [days, setDays] = useState(30);
  const [isGettingLocation, setIsGettingLocation] = useState(false);

  // Fetch nearby incidents
  const { data: incidents, isLoading } = useQuery({
    queryKey: ['nearby', location?.lat, location?.lng, radiusKm, days],
    queryFn: () =>
      incidentService.nearby({
        latitude: location!.lat,
        longitude: location!.lng,
        radius_km: radiusKm,
        days,
      }),
    enabled: !!location,
  });

  const handleGetLocation = async () => {
    setIsGettingLocation(true);
    try {
      const position = await getCurrentLocation();
      const { longitude, latitude } = position.coords;

      setLocation({ lat: latitude, lng: longitude });
      toast.success('Location found!');
    } catch (error) {
      toast.error('Failed to get location. Please enable location services.');
    } finally {
      setIsGettingLocation(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Nearby Incidents</h1>
          <p className="text-gray-600">
            Search for security incidents near your location
          </p>
        </div>

        {/* Search Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Get Location Button */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Location
              </label>
              <button
                onClick={handleGetLocation}
                disabled={isGettingLocation}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-nigeria-green hover:bg-green-700 text-white rounded-md transition-colors disabled:bg-gray-400"
              >
                {isGettingLocation ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Getting location...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                    Use My Location
                  </>
                )}
              </button>
            </div>

            {/* Radius Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Radius
              </label>
              <select
                value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              >
                <option value={5}>5 km</option>
                <option value={10}>10 km</option>
                <option value={20}>20 km</option>
                <option value={50}>50 km</option>
                <option value={100}>100 km</option>
              </select>
            </div>

            {/* Time Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Range
              </label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
            </div>
          </div>

          {/* Current Location Display */}
          {location && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>
                Searching within {radiusKm} km of{' '}
                {formatCoordinates(location.lng, location.lat)}
              </span>
            </div>
          )}
        </div>

        {/* Results */}
        {!location && !isLoading && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            <p className="text-gray-600 mb-2">Click "Use My Location" to find nearby incidents</p>
            <p className="text-sm text-gray-500">
              Your location is only used for this search and is not stored
            </p>
          </div>
        )}

        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nigeria-green mx-auto mb-4"></div>
              <p className="text-gray-600">Searching for nearby incidents...</p>
            </div>
          </div>
        )}

        {incidents && incidents.length > 0 && (
          <>
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Found {incidents.length} incident{incidents.length !== 1 ? 's' : ''} within{' '}
                {radiusKm} km
              </p>
            </div>

            <div className="space-y-4">
              {incidents.map((incident) => (
                <Link
                  key={incident.id}
                  to={`/incidents/${incident.id}`}
                  className="block bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {incidentTypeLabels[incident.incident_type]}
                        </h3>
                        <span className={`severity-badge severity-${incident.severity}`}>
                          {severityLabels[incident.severity]}
                        </span>
                        {incident.verified && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Verified
                          </span>
                        )}
                        {incident.distance_km !== undefined && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                            {incident.distance_km.toFixed(1)} km away
                          </span>
                        )}
                      </div>

                      <p className="text-gray-700 mb-3 line-clamp-2">{incident.description}</p>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                        {incident.location_name && (
                          <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            </svg>
                            {incident.location_name}
                            {incident.state && `, ${incident.state}`}
                          </div>
                        )}

                        <div className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {new Date(incident.timestamp).toLocaleString()}
                        </div>

                        {incident.casualties && (incident.casualties.killed > 0 || incident.casualties.injured > 0) && (
                          <div className="flex items-center gap-1 text-red-600 font-medium">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            {incident.casualties.killed} killed, {incident.casualties.injured} injured
                          </div>
                        )}
                      </div>
                    </div>

                    <svg className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}

        {incidents && incidents.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-600">No incidents found within {radiusKm} km</p>
            <p className="text-sm text-gray-500 mt-1">
              Try increasing the search radius or time range
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
