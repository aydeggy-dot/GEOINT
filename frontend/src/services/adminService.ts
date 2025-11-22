import { API_BASE_URL } from '../config';

export interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  email_verified: boolean;
  status: string;
  roles: string[];
  created_at: string;
  last_login_at: string | null;
}

export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
  created_at: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string | null;
  resource: string;
  action: string;
}

export interface AuditLog {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  status: string;
  details: any;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

export interface IncidentForVerification {
  id: string;
  description: string;
  incident_type: string;
  severity: string;
  location_name: string;
  state: string;
  verified: boolean;
  verification_score: number;
  timestamp: string;
  reporter_id: string;
}

class AdminService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  // User Management
  async getUsers(skip: number = 0, limit: number = 50): Promise<AdminUser[]> {
    const response = await fetch(
      `${API_BASE_URL}/admin/users?skip=${skip}&limit=${limit}`,
      {
        headers: this.getAuthHeader(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch users');
    }

    return response.json();
  }

  async getUser(userId: string): Promise<AdminUser> {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }

    return response.json();
  }

  async updateUserStatus(userId: string, status: string): Promise<AdminUser> {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/status`, {
      method: 'PATCH',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ status }),
    });

    if (!response.ok) {
      throw new Error('Failed to update user status');
    }

    return response.json();
  }

  async assignRole(userId: string, roleId: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/admin/users/${userId}/roles/${roleId}`,
      {
        method: 'POST',
        headers: this.getAuthHeader(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to assign role');
    }
  }

  async removeRole(userId: string, roleId: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/admin/users/${userId}/roles/${roleId}`,
      {
        method: 'DELETE',
        headers: this.getAuthHeader(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to remove role');
    }
  }

  // Role Management
  async getRoles(): Promise<Role[]> {
    const response = await fetch(`${API_BASE_URL}/admin/roles`, {
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch roles');
    }

    return response.json();
  }

  async getPermissions(): Promise<Permission[]> {
    const response = await fetch(`${API_BASE_URL}/admin/permissions`, {
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch permissions');
    }

    return response.json();
  }

  // Incident Verification
  async getUnverifiedIncidents(): Promise<IncidentForVerification[]> {
    const response = await fetch(`${API_BASE_URL}/incidents/?verified=false&limit=100`, {
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch unverified incidents');
    }

    const data = await response.json();
    return data.incidents || [];
  }

  async verifyIncident(incidentId: string, notes?: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${incidentId}/verify`,
      {
        method: 'POST',
        headers: this.getAuthHeader(),
        body: JSON.stringify({ notes }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to verify incident');
    }
  }

  async unverifyIncident(incidentId: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${incidentId}/unverify`,
      {
        method: 'POST',
        headers: this.getAuthHeader(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to unverify incident');
    }
  }

  // Audit Logs
  async getAuditLogs(
    skip: number = 0,
    limit: number = 50,
    userId?: string,
    action?: string,
    resourceType?: string
  ): Promise<AuditLog[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (userId) params.append('user_id', userId);
    if (action) params.append('action', action);
    if (resourceType) params.append('resource_type', resourceType);

    const response = await fetch(`${API_BASE_URL}/admin/audit-logs?${params}`, {
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch audit logs');
    }

    return response.json();
  }

  // Statistics
  async getAdminStats(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/admin/statistics`, {
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch admin stats');
    }

    return response.json();
  }
}

export const adminService = new AdminService();
