import { useState } from 'react';
import IncidentMap from '@/components/IncidentMap';
import {
  IncidentType,
  SeverityLevel,
  incidentTypeLabels,
  severityLabels,
  NIGERIAN_STATES,
} from '@/types/incident';

export default function MapPage() {
  const [days, setDays] = useState(30);
  const [incidentType, setIncidentType] = useState<IncidentType | undefined>();
  const [severity, setSeverity] = useState<SeverityLevel | undefined>();
  const [state, setState] = useState<string | undefined>();
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const handleReset = () => {
    setDays(30);
    setIncidentType(undefined);
    setSeverity(undefined);
    setState(undefined);
    setVerifiedOnly(false);
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-gray-900">Incident Map</h1>

          {/* Time range selector */}
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>

        {/* Filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          Filters
        </button>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Incident Type filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Incident Type
              </label>
              <select
                value={incidentType || ''}
                onChange={(e) =>
                  setIncidentType(e.target.value ? (e.target.value as IncidentType) : undefined)
                }
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

            {/* Severity filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Severity Level
              </label>
              <select
                value={severity || ''}
                onChange={(e) =>
                  setSeverity(e.target.value ? (e.target.value as SeverityLevel) : undefined)
                }
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

            {/* State filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                State
              </label>
              <select
                value={state || ''}
                onChange={(e) => setState(e.target.value || undefined)}
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

            {/* Verified only checkbox */}
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={verifiedOnly}
                  onChange={(e) => setVerifiedOnly(e.target.checked)}
                  className="w-4 h-4 text-nigeria-green border-gray-300 rounded focus:ring-nigeria-green"
                />
                <span className="text-sm text-gray-700">Verified only</span>
              </label>
            </div>
          </div>

          {/* Reset button */}
          <div className="mt-3 flex justify-end">
            <button
              onClick={handleReset}
              className="px-4 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>
      )}

      {/* Map container */}
      <div className="flex-1">
        <IncidentMap
          days={days}
          incidentType={incidentType}
          severity={severity}
          state={state}
          verifiedOnly={verifiedOnly}
        />
      </div>
    </div>
  );
}
