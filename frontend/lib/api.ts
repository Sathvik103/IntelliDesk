import axios from 'axios';
import {
  Organization,
  UserProfile,
  ServiceDomain,
  PredefinedIssue,
  Employee,
  ServiceRequest,
  FeedbackData,
  OverviewKPIs,
  ChartsData,
  CandidateInspectorItem,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('helpdesk_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Authentication APIs
export const apiAuth = {
  login: async (username: string, password: string) => {
    const res = await apiClient.post('/auth/login/', { username, password });
    return res.data;
  },
  register: async (payload: any) => {
    const res = await apiClient.post('/auth/register/', payload);
    return res.data;
  },
  getMe: async (): Promise<UserProfile> => {
    const res = await apiClient.get('/auth/me/');
    return res.data;
  },
};

// Organizations
export const apiOrganizations = {
  list: async (): Promise<Organization[]> => {
    const res = await apiClient.get('/organizations/');
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  create: async (payload: Partial<Organization>): Promise<Organization> => {
    const res = await apiClient.post('/organizations/', payload);
    return res.data;
  },
};

// Services & Domains
export const apiServices = {
  listDomains: async (): Promise<ServiceDomain[]> => {
    const res = await apiClient.get('/services/domains/');
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  listIssues: async (domain: string): Promise<PredefinedIssue[]> => {
    const res = await apiClient.get('/services/issues/', { params: { domain } });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  createDomain: async (payload: Partial<ServiceDomain>): Promise<ServiceDomain> => {
    const res = await apiClient.post('/services/domains/', payload);
    return res.data;
  },
  createIssue: async (payload: Partial<PredefinedIssue>): Promise<PredefinedIssue> => {
    const res = await apiClient.post('/services/issues/', payload);
    return res.data;
  },
};

// Employees
export const apiEmployees = {
  list: async (): Promise<Employee[]> => {
    const res = await apiClient.get('/employees/');
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  getMe: async (): Promise<Employee> => {
    const res = await apiClient.get('/employees/me/');
    return res.data;
  },
  create: async (payload: any): Promise<Employee> => {
    const res = await apiClient.post('/employees/', payload);
    return res.data;
  },
  toggleAvailability: async (id: string, isAvailable?: boolean) => {
    const res = await apiClient.patch(`/employees/${id}/toggle_availability/`, {
      is_available: isAvailable,
    });
    return res.data;
  },
  updateLocation: async (id: string, latitude: number, longitude: number) => {
    const res = await apiClient.patch(`/employees/${id}/update_location/`, {
      latitude,
      longitude,
    });
    return res.data;
  },
};

// Requests
export const apiRequests = {
  list: async (params?: Record<string, any>): Promise<ServiceRequest[]> => {
    const res = await apiClient.get('/requests/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  create: async (payload: any): Promise<ServiceRequest> => {
    const res = await apiClient.post('/requests/', payload);
    return res.data;
  },
  getById: async (id: string): Promise<ServiceRequest> => {
    const res = await apiClient.get(`/requests/${id}/`);
    return res.data;
  },
  startWork: async (id: string) => {
    const res = await apiClient.post(`/requests/${id}/start_work/`);
    return res.data;
  },
  completeWork: async (id: string) => {
    const res = await apiClient.post(`/requests/${id}/complete_work/`);
    return res.data;
  },
  reopen: async (id: string, reason?: string) => {
    const res = await apiClient.post(`/requests/${id}/reopen/`, { reason });
    return res.data;
  },
  triggerAssignment: async (id: string) => {
    const res = await apiClient.post(`/requests/${id}/trigger_assignment/`);
    return res.data;
  },
  inspectCandidates: async (id: string): Promise<{ candidates: CandidateInspectorItem[] }> => {
    const res = await apiClient.get(`/requests/${id}/candidates_preview/`);
    return res.data;
  },
};

// Assignments
export const apiAssignments = {
  accept: async (id: string) => {
    const res = await apiClient.post(`/assignments/${id}/accept/`);
    return res.data;
  },
  reassign: async (id: string, reason?: string) => {
    const res = await apiClient.post(`/assignments/${id}/reassign/`, { reason });
    return res.data;
  },
};

// Feedback
export const apiFeedback = {
  submit: async (payload: { request: string; is_resolved: boolean; rating: number; comments: string }): Promise<FeedbackData> => {
    const res = await apiClient.post('/feedback/', payload);
    return res.data;
  },
};

// Analytics
export const apiAnalytics = {
  getOverview: async (): Promise<OverviewKPIs> => {
    const res = await apiClient.get('/analytics/overview/');
    return res.data;
  },
  getCharts: async (days: number = 14): Promise<ChartsData> => {
    const res = await apiClient.get('/analytics/charts/', { params: { days } });
    return res.data;
  },
  getPlatform: async (): Promise<any> => {
    const res = await apiClient.get('/analytics/platform/');
    return res.data;
  },
};
