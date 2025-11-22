import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { incidentService } from '@/services/api';
import { incidentTypeLabels, severityLabels } from '@/types/incident';
import { formatCoordinates } from '@/utils/mapConfig';

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();

  // Fetch incident details
  const { data: incident, isLoading, error } = useQuery({
    queryKey: ['incident', id],
    queryFn: () => incidentService.getById(id!),
    enabled: !!id,
  });

  // Fetch nearby incidents
  const { data: nearbyIncidents } = useQuery({
    queryKey: ['nearby-incidents', incident?.location.coordinates],
    queryFn: () =>
      incidentService.nearby({
        latitude: incident!.location.coordinates[1],
        longitude: incident!.location.coordinates[0],
        radius_km: 20,
        days: 30,
      }),
    enabled: !!incident,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nigeria-green mx-auto mb-4"></div>
          <p className="text-gray-600">Loading incident details...</p>
        </div>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          <p>Incident not found or failed to load.</p>
          <Link to="/incidents" className="text-red-900 underline mt-2 inline-block">
            Back to incidents list
          </Link>
        </div>
      </div>
    );
  }

  const [lng, lat] = incident.location.coordinates;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Link
          to="/incidents"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to all incidents
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {incidentTypeLabels[incident.incident_type]}
                    </h1>
                    <span className={`severity-badge severity-${incident.severity}`}>
                      {severityLabels[incident.severity]}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">Incident ID: {incident.id}</p>
                </div>

                {incident.verified ? (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-800 rounded-full">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-sm font-medium">Verified</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-100 text-yellow-800 rounded-full">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-sm font-medium">Unverified</span>
                  </div>
                )}
              </div>

              <div className="prose max-w-none">
                <p className="text-gray-700 leading-relaxed">{incident.description}</p>
              </div>
            </div>

            {/* Details Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Incident Details</h2>

              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1">Date & Time</dt>
                  <dd className="text-sm text-gray-900">
                    {new Date(incident.timestamp).toLocaleString('en-NG', {
                      dateStyle: 'full',
                      timeStyle: 'short',
                    })}
                  </dd>
                </div>

                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1">Location</dt>
                  <dd className="text-sm text-gray-900">
                    {incident.location_name || formatCoordinates(lng, lat)}
                    {incident.state && (
                      <div className="text-xs text-gray-500 mt-1">{incident.state}</div>
                    )}
                    {incident.lga && (
                      <div className="text-xs text-gray-500">{incident.lga} LGA</div>
                    )}
                  </dd>
                </div>

                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1">Coordinates</dt>
                  <dd className="text-sm text-gray-900 font-mono">
                    {formatCoordinates(lng, lat)}
                  </dd>
                </div>

                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1">Verification Score</dt>
                  <dd className="text-sm text-gray-900">
                    {Math.round(incident.verification_score * 100)}%
                  </dd>
                </div>

                {incident.casualties && (
                  <div className="md:col-span-2">
                    <dt className="text-sm font-medium text-gray-500 mb-2">Casualties</dt>
                    <dd className="grid grid-cols-3 gap-4">
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <div className="text-2xl font-bold text-red-600">
                          {incident.casualties.killed}
                        </div>
                        <div className="text-xs text-red-800">Killed</div>
                      </div>
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                        <div className="text-2xl font-bold text-orange-600">
                          {incident.casualties.injured}
                        </div>
                        <div className="text-xs text-orange-800">Injured</div>
                      </div>
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                        <div className="text-2xl font-bold text-yellow-600">
                          {incident.casualties.missing}
                        </div>
                        <div className="text-xs text-yellow-800">Missing</div>
                      </div>
                    </dd>
                  </div>
                )}

                {incident.tags && incident.tags.length > 0 && (
                  <div className="md:col-span-2">
                    <dt className="text-sm font-medium text-gray-500 mb-2">Tags</dt>
                    <dd className="flex flex-wrap gap-2">
                      {incident.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2.5 py-0.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Media */}
            {incident.media_urls && incident.media_urls.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Media</h2>
                <div className="space-y-2">
                  {incident.media_urls.map((url, index) => (
                    <a
                      key={index}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-nigeria-green hover:underline"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Media {index + 1}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Map Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Location Map</h2>
              <div className="aspect-square rounded-lg overflow-hidden bg-gray-100">
                <iframe
                  src={`https://www.openstreetmap.org/export/embed.html?bbox=${lng-0.01},${lat-0.01},${lng+0.01},${lat+0.01}&layer=mapnik&marker=${lat},${lng}`}
                  width="100%"
                  height="100%"
                  style={{ border: 0 }}
                  title="Incident location map"
                />
              </div>
              <a
                href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=15/${lat}/${lng}`}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex items-center gap-2 text-sm text-nigeria-green hover:underline"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                View on OpenStreetMap
              </a>
            </div>

            {/* Nearby Incidents */}
            {nearbyIncidents && nearbyIncidents.length > 1 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Nearby Incidents ({nearbyIncidents.length - 1})
                </h2>
                <div className="space-y-3">
                  {nearbyIncidents
                    .filter((nearby) => nearby.id !== incident.id)
                    .slice(0, 5)
                    .map((nearby) => (
                      <Link
                        key={nearby.id}
                        to={`/incidents/${nearby.id}`}
                        className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`severity-badge severity-${nearby.severity} text-xs`}>
                            {severityLabels[nearby.severity]}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-gray-900">
                          {incidentTypeLabels[nearby.incident_type]}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {nearby.distance_km && `${nearby.distance_km.toFixed(1)} km away • `}
                          {new Date(nearby.timestamp).toLocaleDateString()}
                        </p>
                      </Link>
                    ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="bg-gray-100 rounded-lg p-4 text-xs text-gray-600">
              <p>
                Reported: {incident.created_at && new Date(incident.created_at).toLocaleString()}
              </p>
              {incident.updated_at && incident.updated_at !== incident.created_at && (
                <p className="mt-1">
                  Updated: {new Date(incident.updated_at).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
