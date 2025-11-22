import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { incidentService } from '@/services/api';
import {
  IncidentType,
  SeverityLevel,
  incidentTypeLabels,
  severityLabels,
  NIGERIAN_STATES,
} from '@/types/incident';

export default function IncidentListPage() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [incidentType, setIncidentType] = useState<IncidentType | undefined>();
  const [severity, setSeverity] = useState<SeverityLevel | undefined>();
  const [state, setState] = useState<string | undefined>();
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [days, setDays] = useState(30);

  // Fetch incidents
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', page, pageSize, incidentType, severity, state, verifiedOnly, days],
    queryFn: () =>
      incidentService.list({
        page,
        page_size: pageSize,
        incident_type: incidentType,
        severity,
        state,
        verified_only: verifiedOnly,
        days,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  // Handle CSV export
  const handleExportCSV = () => {
    // Build query parameters
    const params = new URLSearchParams();
    params.append('days', days.toString());

    if (incidentType) {
      params.append('incident_type', incidentType);
    }
    if (severity) {
      params.append('severity', severity);
    }
    if (state) {
      params.append('state', state);
    }
    if (verifiedOnly) {
      params.append('verified_only', 'true');
    }

    // Get the API base URL from environment or default
    const apiBaseUrl = import.meta.env.VITE_API_URL || '/api/v1';
    const exportUrl = `${apiBaseUrl}/incidents/export/csv?${params.toString()}`;

    // Trigger download
    window.open(exportUrl, '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">All Incidents</h1>
            <p className="text-gray-600">
              Browse and filter security incidents reported across Nigeria
            </p>
          </div>
          <button
            onClick={() => handleExportCSV()}
            className="px-4 py-2 bg-nigeria-green text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Time Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Time Range
              </label>
              <select
                value={days}
                onChange={(e) => {
                  setDays(Number(e.target.value));
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
            </div>

            {/* Incident Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Incident Type
              </label>
              <select
                value={incidentType || ''}
                onChange={(e) => {
                  setIncidentType(e.target.value ? (e.target.value as IncidentType) : undefined);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              >
                <option value="">All Types</option>
                {Object.entries(incidentTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Severity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
              <select
                value={severity || ''}
                onChange={(e) => {
                  setSeverity(e.target.value ? (e.target.value as SeverityLevel) : undefined);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              >
                <option value="">All Levels</option>
                {Object.entries(severityLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* State */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <select
                value={state || ''}
                onChange={(e) => {
                  setState(e.target.value || undefined);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              >
                <option value="">All States</option>
                {NIGERIAN_STATES.map((stateName) => (
                  <option key={stateName} value={stateName}>
                    {stateName}
                  </option>
                ))}
              </select>
            </div>

            {/* Verified Only */}
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={verifiedOnly}
                  onChange={(e) => {
                    setVerifiedOnly(e.target.checked);
                    setPage(1);
                  }}
                  className="w-4 h-4 text-nigeria-green border-gray-300 rounded focus:ring-nigeria-green"
                />
                <span className="text-sm text-gray-700">Verified only</span>
              </label>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nigeria-green mx-auto mb-4"></div>
              <p className="text-gray-600">Loading incidents...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
            <p>Failed to load incidents. Please try again later.</p>
          </div>
        )}

        {/* Incidents List */}
        {data && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, data.total)} of {data.total} incidents
              </p>
            </div>

            <div className="space-y-4 mb-6">
              {data.incidents.map((incident) => (
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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                >
                  Previous
                </button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`w-10 h-10 rounded-md text-sm font-medium ${
                          page === pageNum
                            ? 'bg-nigeria-green text-white'
                            : 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}

            {/* No Results */}
            {data.incidents.length === 0 && (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-600">No incidents found matching your filters</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
