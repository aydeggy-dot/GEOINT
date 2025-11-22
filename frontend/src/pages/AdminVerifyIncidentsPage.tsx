import { useEffect, useState } from 'react';
import { adminService, IncidentForVerification } from '../services/adminService';
import { toast } from 'sonner';

export default function AdminVerifyIncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentForVerification[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<IncidentForVerification | null>(null);
  const [verificationNotes, setVerificationNotes] = useState('');
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await adminService.getUnverifiedIncidents();
      setIncidents(data);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load incidents');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!selectedIncident) return;

    try {
      await adminService.verifyIncident(selectedIncident.id, verificationNotes);
      toast.success('Incident verified successfully');
      setShowModal(false);
      setSelectedIncident(null);
      setVerificationNotes('');
      loadIncidents();
    } catch (error: any) {
      toast.error(error.message || 'Failed to verify incident');
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      LOW: 'bg-yellow-100 text-yellow-800',
      MODERATE: 'bg-orange-100 text-orange-800',
      HIGH: 'bg-red-100 text-red-800',
      CRITICAL: 'bg-purple-100 text-purple-800',
    };
    return colors[severity] || 'bg-gray-100 text-gray-800';
  };

  const getTypeLabel = (type: string) => {
    return type.split('_').map(word =>
      word.charAt(0) + word.slice(1).toLowerCase()
    ).join(' ');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading incidents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Incident Verification</h1>
        <p className="mt-2 text-gray-600">
          Review and verify submitted security incidents ({incidents.length} pending)
        </p>
      </div>

      {/* Incidents List */}
      {incidents.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">✓</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            All caught up!
          </h3>
          <p className="text-gray-600">There are no incidents pending verification.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {incidents.map((incident) => (
            <div
              key={incident.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-center space-x-3 mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getSeverityColor(incident.severity)}`}>
                      {incident.severity}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                      {getTypeLabel(incident.incident_type)}
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(incident.timestamp).toLocaleString()}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-gray-900 text-lg mb-3">{incident.description}</p>

                  {/* Location */}
                  <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                    <span>📍 {incident.location_name}</span>
                    <span>• {incident.state}</span>
                  </div>

                  {/* Verification Score */}
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-700">
                      Verification Score:
                    </span>
                    <div className="flex-1 max-w-xs bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          incident.verification_score > 0.7
                            ? 'bg-green-500'
                            : incident.verification_score > 0.4
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${incident.verification_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">
                      {(incident.verification_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="ml-6">
                  <button
                    onClick={() => {
                      setSelectedIncident(incident);
                      setShowModal(true);
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Verify
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Verification Modal */}
      {showModal && selectedIncident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Verify Incident
            </h3>

            {/* Incident Details */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex items-center space-x-3 mb-2">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getSeverityColor(selectedIncident.severity)}`}>
                  {selectedIncident.severity}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                  {getTypeLabel(selectedIncident.incident_type)}
                </span>
              </div>
              <p className="text-gray-900 mb-2">{selectedIncident.description}</p>
              <p className="text-sm text-gray-600">
                📍 {selectedIncident.location_name}, {selectedIncident.state}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                🕒 {new Date(selectedIncident.timestamp).toLocaleString()}
              </p>
            </div>

            {/* Notes Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Verification Notes (Optional)
              </label>
              <textarea
                value={verificationNotes}
                onChange={(e) => setVerificationNotes(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Add any notes about the verification..."
              />
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={handleVerify}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Verify Incident
              </button>
              <button
                onClick={() => {
                  setShowModal(false);
                  setSelectedIncident(null);
                  setVerificationNotes('');
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
