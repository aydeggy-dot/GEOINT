/**
 * Authentication Service
 * Handles all authentication-related API calls
 */

import type {
  LoginCredentials,
  RegisterData,
  TokenResponse,
  User,
  TwoFactorSetupResponse,
  TwoFactorStatus,
  PasswordResetRequest,
  PasswordResetConfirm,
  ChangePasswordRequest,
} from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    // Load tokens from localStorage on initialization
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  /**
   * Set authentication tokens
   */
  setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  /**
   * Clear authentication tokens
   */
  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  /**
   * Get authorization header
   */
  private getAuthHeader(): HeadersInit {
    if (this.accessToken) {
      return {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
      };
    }
    return { 'Content-Type': 'application/json' };
  }

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<{ message: string; email: string }> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  /**
   * Login with email and password
   * @param credentials - Login credentials (email, password, optional 2FA code)
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (response.status === 403) {
      const error = await response.json();
      if (error.detail?.includes('Two-factor')) {
        // 2FA required
        throw new Error('2FA_REQUIRED');
      }
      throw new Error(error.detail || 'Login failed');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data: TokenResponse = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  /**
   * Logout (revoke current session)
   */
  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeader(),
      });
    } finally {
      this.clearTokens();
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.clearTokens();
      }
      throw new Error('Failed to get user profile');
    }

    return response.json();
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<TokenResponse> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error('Token refresh failed');
    }

    const data: TokenResponse = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  /**
   * Change password
   */
  async changePassword(data: ChangePasswordRequest): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Password change failed');
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Password reset request failed');
    }
  }

  /**
   * Reset password with token
   */
  async resetPassword(data: PasswordResetConfirm): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Password reset failed');
    }
  }

  // ==================== 2FA Methods ====================

  /**
   * Get 2FA status
   */
  async get2FAStatus(): Promise<TwoFactorStatus> {
    const response = await fetch(`${API_BASE_URL}/2fa/status`, {
      method: 'GET',
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to get 2FA status');
    }

    return response.json();
  }

  /**
   * Setup 2FA (get secret and QR code)
   */
  async setup2FA(): Promise<TwoFactorSetupResponse> {
    const response = await fetch(`${API_BASE_URL}/2fa/setup`, {
      method: 'POST',
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '2FA setup failed');
    }

    return response.json();
  }

  /**
   * Enable 2FA with verification code
   */
  async enable2FA(code: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/2fa/enable`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ code }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '2FA enable failed');
    }
  }

  /**
   * Disable 2FA
   */
  async disable2FA(password: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/2fa/disable`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '2FA disable failed');
    }
  }

  /**
   * Regenerate backup codes
   */
  async regenerateBackupCodes(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/2fa/regenerate-codes`, {
      method: 'POST',
      headers: this.getAuthHeader(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to regenerate backup codes');
    }

    const data = await response.json();
    return data.backup_codes;
  }

  /**
   * Verify 2FA code
   */
  async verify2FA(code: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/2fa/verify`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ code }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '2FA verification failed');
    }
  }
}

export const authService = new AuthService();
export default authService;
