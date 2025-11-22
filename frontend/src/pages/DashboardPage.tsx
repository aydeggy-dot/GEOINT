import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { incidentService } from '@/services/api';
import { incidentTypeLabels, severityLabels } from '@/types/incident';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const SEVERITY_COLORS = {
  critical: '#DC2626',
  high: '#EA580C',
  moderate: '#F59E0B',
  low: '#16A34A',
};

export default function DashboardPage() {
  const [days, setDays] = useState(30);

  // Fetch statistics
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['incident-stats', days],
    queryFn: () => incidentService.stats(days),
    refetchInterval: 60000, // Refetch every minute
  });

  // Fetch time series data
  const { data: timeseries } = useQuery({
    queryKey: ['incident-timeseries', days],
    queryFn: () => incidentService.timeseries(days, 'day'),
    refetchInterval: 60000,
  });

  // Fetch recent incidents
  const { data: recentIncidents } = useQuery({
    queryKey: ['recent-incidents'],
    queryFn: () => incidentService.recent(8),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nigeria-green mx-auto mb-4"></div>
          <p className="text-gray-600">Loading statistics...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          <p>Failed to load statistics. Please try again later.</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const incidentTypeData = Object.entries(stats.by_type).map(([type, count]) => ({
    name: incidentTypeLabels[type as keyof typeof incidentTypeLabels] || type,
    value: count,
  }));

  const severityData = Object.entries(stats.by_severity).map(([severity, count]) => ({
    name: severityLabels[severity as keyof typeof severityLabels] || severity,
    value: count,
    color: SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || '#6B7280',
  }));

  const topStates = Object.entries(stats.by_state)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([state, count]) => ({ state, count }));

  // Prepare time series data
  const timeseriesChartData = timeseries?.series.map((item: any) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    Total: item.total,
    Critical: item.critical,
    High: item.high,
    Moderate: item.moderate,
    Low: item.low,
  })) || [];

  // Helper function to render change indicator
  const ChangeIndicator = ({ value }: { value: number | null | undefined }) => {
    if (value === null || value === undefined) return null;

    const isPositive = value > 0;
    const isNegative = value < 0;
    const isNeutral = value === 0;

    if (isNeutral) {
      return (
        <span className="text-xs text-gray-500 flex items-center gap-1">
          <span>—</span>
          <span>No change</span>
        </span>
      );
    }

    return (
      <span className={`text-xs flex items-center gap-1 ${
        isPositive ? 'text-red-600' : 'text-green-600'
      }`}>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isPositive ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          )}
        </svg>
        <span>{Math.abs(value).toFixed(1)}%</span>
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Security Dashboard</h1>
            <p className="text-gray-600">
              Overview of security incidents across Nigeria
            </p>
          </div>

          {/* Time range selector */}
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Incidents */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Incidents</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.total_incidents}
                </p>
                <div className="mt-2">
                  <ChangeIndicator value={stats.total_incidents_change} />
                </div>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Verified Incidents */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Verified</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  {stats.verified_count}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {Math.round((stats.verified_count / stats.total_incidents) * 100)}% of total
                </p>
                <div className="mt-1">
                  <ChangeIndicator value={stats.verified_count_change} />
                </div>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Total Casualties */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Casualties</p>
                <p className="text-3xl font-bold text-red-600 mt-2">
                  {stats.casualties_total.killed + stats.casualties_total.injured}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {stats.casualties_total.killed} killed, {stats.casualties_total.injured} injured
                </p>
                <div className="mt-1">
                  <ChangeIndicator value={stats.casualties_change} />
                </div>
              </div>
              <div className="p-3 bg-red-100 rounded-lg">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Missing Persons */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Missing Persons</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">
                  {stats.casualties_total.missing}
                </p>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Time Series Trend Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Incidents Over Time</h2>
          {timeseriesChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeseriesChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} fontSize={11} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="Total" stroke="#008751" strokeWidth={2} />
                <Line type="monotone" dataKey="Critical" stroke="#DC2626" strokeWidth={1.5} />
                <Line type="monotone" dataKey="High" stroke="#EA580C" strokeWidth={1.5} />
                <Line type="monotone" dataKey="Moderate" stroke="#F59E0B" strokeWidth={1.5} />
                <Line type="monotone" dataKey="Low" stroke="#16A34A" strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">Loading trend data...</p>
          )}
        </div>

        {/* Recent Incidents Feed */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Incidents</h2>
            <Link to="/incidents" className="text-sm text-nigeria-green hover:text-green-700 font-medium">
              View all →
            </Link>
          </div>
          {recentIncidents && recentIncidents.length > 0 ? (
            <div className="space-y-3">
              {recentIncidents.map((incident) => (
                <Link
                  key={incident.id}
                  to={`/incidents/${incident.id}`}
                  className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`severity-badge severity-${incident.severity}`}>
                          {severityLabels[incident.severity]}
                        </span>
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {incidentTypeLabels[incident.incident_type]}
                        </span>
                        {incident.verified && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">
                            ✓
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-1">{incident.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {incident.state} • {new Date(incident.timestamp).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No recent incidents</p>
          )}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Incidents by Type */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Incidents by Type</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={incidentTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#008751" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Incidents by Severity */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Incidents by Severity</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top States by Incidents */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 States by Incidents</h2>
          <div className="space-y-3">
            {topStates.map((item, index) => (
              <div key={item.state} className="flex items-center gap-4">
                <div className="w-8 h-8 flex items-center justify-center bg-nigeria-green text-white rounded-full font-semibold text-sm">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900">{item.state}</span>
                    <span className="text-sm text-gray-600">{item.count} incidents</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-nigeria-green h-2 rounded-full transition-all"
                      style={{
                        width: `${(item.count / topStates[0].count) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Time Range Info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>
            Showing data from {new Date(stats.time_range_start).toLocaleDateString()} to{' '}
            {new Date(stats.time_range_end).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
}
