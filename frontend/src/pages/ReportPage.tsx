import { useNavigate } from 'react-router-dom';
import IncidentReportForm from '@/components/IncidentReportForm';

export default function ReportPage() {
  const navigate = useNavigate();

  const handleSuccess = () => {
    // Redirect to map after successful submission
    setTimeout(() => {
      navigate('/');
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Report Security Incident</h1>
          <p className="text-gray-600">
            Help improve community safety by reporting security incidents in your area.
            Your report will help authorities and the community stay informed.
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <IncidentReportForm onSuccess={handleSuccess} />
        </div>

        {/* Help Section */}
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="text-sm font-semibold text-yellow-900 mb-2">
            Reporting Guidelines
          </h3>
          <ul className="text-sm text-yellow-800 space-y-1">
            <li>• Only report incidents that occurred within Nigeria</li>
            <li>• Provide accurate and truthful information</li>
            <li>• Include as many details as possible to help verification</li>
            <li>• For emergencies, please contact local authorities immediately</li>
          </ul>
        </div>

        {/* Emergency Contacts */}
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-sm font-semibold text-red-900 mb-2">
            Emergency Contacts
          </h3>
          <div className="text-sm text-red-800 space-y-1">
            <p>• Police Emergency: 112 or 199</p>
            <p>• Fire Service: 112</p>
            <p>• Ambulance: 112</p>
          </div>
        </div>
      </div>
    </div>
  );
}
