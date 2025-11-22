import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { adminService } from '../services/adminService';
import { toast } from 'sonner';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await adminService.getAdminStats();
      setStats(data);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load admin statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-gray-600">Manage users, roles, and system settings</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon="👥"
          color="blue"
        />
        <StatCard
          title="Active Users"
          value={stats?.active_users || 0}
          icon="✓"
          color="green"
        />
        <StatCard
          title="Pending Verifications"
          value={stats?.pending_verifications || 0}
          icon="⏱"
          color="yellow"
        />
        <StatCard
          title="Total Roles"
          value={stats?.total_roles || 6}
          icon="🔐"
          color="purple"
        />
      </div>

      {/* Quick Actions Grid */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ActionCard
            title="User Management"
            description="View and manage all users, assign roles, and update statuses"
            link="/admin/users"
            icon="👥"
            color="blue"
          />
          <ActionCard
            title="Incident Verification"
            description="Review and verify submitted security incidents"
            link="/admin/incidents/verify"
            icon="✓"
            color="green"
          />
          <ActionCard
            title="Audit Logs"
            description="View system audit logs and user activities"
            link="/admin/audit-logs"
            icon="📋"
            color="purple"
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">System Information</h2>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="System Status" value="Operational" valueClass="text-green-600" />
            <InfoRow label="Database" value="Connected" valueClass="text-green-600" />
            <InfoRow label="API Version" value="v1.0.0" />
            <InfoRow label="Total Incidents" value={stats?.total_incidents || 0} />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: string; color: string }) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color as keyof typeof colorClasses]}`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

function ActionCard({
  title,
  description,
  link,
  icon,
  color,
}: {
  title: string;
  description: string;
  link: string;
  icon: string;
  color: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-600 hover:bg-blue-700',
    green: 'bg-green-600 hover:bg-green-700',
    purple: 'bg-purple-600 hover:bg-purple-700',
  };

  return (
    <Link
      to={link}
      className="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
    >
      <div className="flex items-start space-x-4">
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]} text-white`}>
          <span className="text-2xl">{icon}</span>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
    </Link>
  );
}

function InfoRow({ label, value, valueClass = 'text-gray-900' }: { label: string; value: string | number; valueClass?: string }) {
  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-sm font-medium text-gray-600">{label}:</span>
      <span className={`text-sm font-semibold ${valueClass}`}>{value}</span>
    </div>
  );
}
