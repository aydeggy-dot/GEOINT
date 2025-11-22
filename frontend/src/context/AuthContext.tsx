/**
 * Authentication Context
 * Provides global authentication state and methods
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/authService';
import type {
  User,
  LoginCredentials,
  RegisterData,
  TokenResponse,
  AuthState,
} from '../types/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
    isAuthenticated: false,
    isLoading: true,
    requires2FA: false,
    tempCredentials: null,
  });

  /**
   * Initialize auth state on mount
   */
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const user = await authService.getCurrentUser();
          setState(prev => ({
            ...prev,
            user,
            isAuthenticated: true,
            isLoading: false,
          }));
        } catch (error) {
          // Token invalid or expired
          console.error('Auth initialization failed:', error);
          authService.clearTokens();
          setState(prev => ({
            ...prev,
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
          }));
        }
      } else {
        setState(prev => ({ ...prev, isLoading: false }));
      }
    };

    initAuth();
  }, []);

  /**
   * Login user
   */
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const response: TokenResponse = await authService.login(credentials);

      setState({
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        requires2FA: false,
        tempCredentials: null,
      });
    } catch (error) {
      if (error instanceof Error && error.message === '2FA_REQUIRED') {
        // Store credentials temporarily for 2FA step
        setState(prev => ({
          ...prev,
          requires2FA: true,
          tempCredentials: credentials,
          isLoading: false,
        }));
        throw new Error('Two-factor authentication required');
      }
      throw error;
    }
  };

  /**
   * Register new user
   */
  const register = async (data: RegisterData): Promise<void> => {
    await authService.register(data);
    // Note: User will need to verify email before logging in
  };

  /**
   * Logout user
   */
  const logout = async (): Promise<void> => {
    await authService.logout();
    setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      requires2FA: false,
      tempCredentials: null,
    });
  };

  /**
   * Refresh current user data
   */
  const refreshUser = async (): Promise<void> => {
    try {
      const user = await authService.getCurrentUser();
      setState(prev => ({
        ...prev,
        user,
      }));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // Token might be expired, logout
      await logout();
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to use authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
