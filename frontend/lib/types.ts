export type RoleType = 'ADMIN' | 'EMPLOYEE' | 'USER';

export type OrgType = 
  | 'RESIDENTIAL_COLONY' 
  | 'GATED_COMMUNITY' 
  | 'OFFICE_SPACE' 
  | 'COMMERCIAL_COMPLEX' 
  | 'EDUCATIONAL_CAMPUS' 
  | 'OTHER';

export type PriorityType = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT' | 'CRITICAL';

export type RequestStatusType = 
  | 'CREATED' 
  | 'QUEUED' 
  | 'ASSIGNED' 
  | 'IN_PROGRESS' 
  | 'COMPLETED' 
  | 'REOPENED' 
  | 'CANCELLED';

export type AssignmentStatusType = 
  | 'ASSIGNED' 
  | 'ACCEPTED' 
  | 'IN_PROGRESS' 
  | 'COMPLETED' 
  | 'REASSIGNED' 
  | 'CANCELLED';

export interface Organization {
  id: string;
  name: string;
  org_type: OrgType;
  org_type_display?: string;
  address: string;
  latitude: number;
  longitude: number;
  contact_email: string;
  contact_phone: string;
  is_active: boolean;
  created_at: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: RoleType;
  role_display: string;
  organization?: string;
  organization_details?: Organization;
  phone?: string;
  address?: string;
  is_active: boolean;
  is_superuser?: boolean;
  is_staff?: boolean;
  created_at: string;
}

export interface PredefinedIssue {
  id: string;
  domain: string;
  domain_name?: string;
  title: string;
  default_priority: PriorityType;
  default_priority_display?: string;
  estimated_duration_minutes: number;
  is_active: boolean;
}

export interface ServiceDomain {
  id: string;
  organization: string;
  organization_name?: string;
  name: string;
  description: string;
  sla_hours: number;
  icon_name: string;
  is_active: boolean;
  predefined_issues?: PredefinedIssue[];
  employee_count?: number;
}

export interface EmployeeRole {
  id: string;
  organization: string;
  title: string;
  description: string;
}

export interface EmployeeSkill {
  id: string;
  employee: string;
  domain: string;
  domain_name: string;
  proficiency_level: number;
  years_of_experience: number;
}

export interface EmployeeSchedule {
  id: string;
  employee: string;
  day_of_week: number;
  day_name: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface Employee {
  id: string;
  user: string;
  user_details: UserProfile;
  organization: string;
  role?: string;
  role_details?: EmployeeRole;
  experience_years: number;
  max_active_assignments: number;
  current_latitude: number;
  current_longitude: number;
  status: 'ACTIVE' | 'ON_LEAVE' | 'OFF_DUTY' | 'INACTIVE';
  status_display: string;
  is_available: boolean;
  skills: EmployeeSkill[];
  schedules?: EmployeeSchedule[];
  active_assignments_count: number;
  historical_avg_rating: number;
  historical_completed_count: number;
  last_location_updated_at?: string;
}

export interface ActiveAssignment {
  id: string;
  employee_id: string;
  employee_name: string;
  employee_phone?: string;
  role_title?: string;
  status: AssignmentStatusType;
  distance_km: number;
  suitability_score: number;
  ranking_model_version: string;
  assigned_at: string;
  completed_at?: string;
}

export interface FeedbackData {
  id: string;
  request: string;
  request_description?: string;
  user: string;
  user_name?: string;
  employee: string;
  employee_name?: string;
  is_resolved: boolean;
  rating: number;
  comments: string;
  resolution_time_minutes: number;
  met_sla: boolean;
  created_at: string;
}

export interface ServiceRequest {
  id: string;
  organization: string;
  user: string;
  user_details?: UserProfile;
  domain: string;
  domain_details?: ServiceDomain;
  predefined_issue?: string;
  predefined_issue_details?: PredefinedIssue;
  custom_description: string;
  details_snapshot?: Record<string, unknown>;
  latitude: number;
  longitude: number;
  location_name: string;
  priority: PriorityType;
  priority_display: string;
  status: RequestStatusType;
  status_display: string;
  active_assignment?: ActiveAssignment | null;
  feedback_details?: FeedbackData | null;
  created_at: string;
  in_progress_at?: string;
  completed_at?: string;
  updated_at: string;
}

export interface CandidateInspectorItem {
  employee_id: string;
  employee_name: string;
  role_title: string;
  distance_km: number;
  suitability_score: number;
  current_active_jobs: number;
  domain_proficiency: number;
  historical_avg_rating: number;
  features: Record<string, any>;
}

export interface OverviewKPIs {
  total_requests: number;
  open_requests: number;
  in_progress_requests: number;
  active_requests?: number;
  completed_requests: number;
  urgent_requests: number;
  critical_requests: number;
  avg_resolution_time_mins: number;
  avg_rating: number;
  sla_compliance_rate: number;
  resolution_rate: number;
  total_employees: number;
  available_employees: number;
  unavailable_employees?: number;
  employees_at_capacity?: number;
}

export interface ChartsData {
  by_domain: Array<{ domain: string; count: number; completed: number }>;
  by_priority: Array<{ priority: string; count: number }>;
  by_status: Array<{ status: string; count: number }>;
  daily_trend: Array<{ date: string; created: number; completed: number }>;
  satisfaction_breakdown: Array<{ stars: string; rating: number; count: number }>;
  workforce_performance: Array<{
    id: string;
    name: string;
    email?: string;
    role: string;
    status: string;
    is_available: boolean;
    current_active: number;
    max_capacity: number;
    workload_pct: number;
    completed_total: number;
    completion_rate?: number;
    avg_rating: number;
    avg_resolution_mins: number;
    sla_compliance_pct: number;
    skills: string[];
  }>;
}
