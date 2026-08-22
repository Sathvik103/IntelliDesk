'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, Organization, RoleType } from '@/lib/types';
import { apiAuth, apiOrganizations, apiClient } from '@/lib/api';

interface AuthContextType {
  user: UserProfile | null;
  role: RoleType;
  token: string | null;
  organization: Organization | null;
  allOrganizations: Organization[];
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setOrganization: (org: Organization) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [allOrganizations, setAllOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        const savedToken = localStorage.getItem('helpdesk_access_token');
        if (savedToken) {
          setToken(savedToken);
          try {
            // 1. Validate token by fetching user profile
            const profile = await apiAuth.getMe();
            setUser(profile);
            if (profile.organization_details) {
              setOrganization(profile.organization_details);
            }

            // 2. Only AFTER user is confirmed authenticated, load organizations
            try {
              const orgs = await apiOrganizations.list();
              setAllOrganizations(orgs);
            } catch (orgErr) {
              console.warn('Failed to load organizations after authentication.', orgErr);
            }
          } catch (err) {
            console.warn('Session expired or offline. Clearing saved token.');
            localStorage.removeItem('helpdesk_access_token');
            setToken(null);
          }
        }
        // If no saved token, do NOT call authenticated endpoints
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await apiAuth.login(username, password);
      localStorage.setItem('helpdesk_access_token', data.access);
      setToken(data.access);
      setUser(data.user);
      if (data.user.organization_details) {
        setOrganization(data.user.organization_details);
      }
      // Load all organizations for the org selector
      try {
        const orgs = await apiOrganizations.list();
        setAllOrganizations(orgs);
      } catch (orgErr) {
        console.warn('Failed to load organizations after login.', orgErr);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('helpdesk_access_token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const profile = await apiAuth.getMe();
      setUser(profile);
      if (profile.organization_details) {
        setOrganization(profile.organization_details);
      }
    } catch (err) {
      console.warn('Could not refresh profile', err);
    }
  };

  const activeRole: RoleType = user?.role || 'USER';

  return (
    <AuthContext.Provider
      value={{
        user,
        role: activeRole,
        token,
        organization,
        allOrganizations,
        isLoading,
        login,
        logout,
        setOrganization,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
