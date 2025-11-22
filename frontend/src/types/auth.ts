/**
 * Authentication Types
 * Type definitions for auth-related data structures
 */

export interface User {
  id: string;
  email: string;
  name: string | null;
  email_verified: boolean;
  phone_number: string | null;
  phone_verified: boolean;
  is_active: boolean;
  status: 'active' | 'suspended' | 'inactive';
  trust_score: number;
  is_verified_reporter: boolean;
  roles: string[];
  created_at: string;
  last_login_at: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
  two_factor_code?: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TwoFactorSetupResponse {
  secret: string;
  qr_code: string;
  backup_codes: string[];
  message: string;
}

export interface TwoFactorStatus {
  enabled: boolean;
  method: 'totp' | 'email' | null;
  backup_codes_remaining: number;
}

export interface AuthError {
  detail: string;
  requires_2fa?: boolean;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  requires2FA: boolean;
  tempCredentials: LoginCredentials | null;
}
