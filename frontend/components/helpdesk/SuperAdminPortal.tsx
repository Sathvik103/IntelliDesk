'use client';

import React, { useState, useEffect } from 'react';
import {
  Organization,
  UserProfile,
  ServiceRequest,
} from '@/lib/types';
import {
  apiAnalytics,
  apiOrganizations,
} from '@/lib/api';
import {
  Building2,
  Users,
  TrendingUp,
  Settings,
  BarChart3,
  Search,
  Filter,
  Eye,
  RefreshCw,
  Activity,
  Clock,
  Star,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Award,
  Globe,
  Zap,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { Sidebar } from './ui/Sidebar';
import { KPICard } from './ui/KPICard';
import { EmptyState } from './ui/EmptyState';
import { SkeletonCard, SkeletonTable } from './ui/SkeletonLoader';

type Section = 'dashboard' | 'organizations' | 'users' | 'analytics';

interface PlatformKPIs {
  total_organizations: number;
  active_organizations: number;
  total_users: number;
  total_employees: number;
  total_requests: number;
  completion_rate: number;
  avg_resolution_time_hours: number;
  overall_satisfaction_rating: number;
  requests_by_organization?: Array<{ organization_name: string; count: number }>;
  requests_by_domain?: Array<{ domain: string; count: number }>;
  requests_by_status?: Array<{ status: string; count: number }>;
}

// ─── Dashboard Section ───────────────────────────────────────────────────────────
const DashboardSection: React.FC<{ kpis: PlatformKPIs | null; loading: boolean }> = ({ kpis, loading }) => {
  if (loading) {
    return <div className="row g-3">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="col-6 col-md-3"><SkeletonCard /></div>)}</div>;
  }

  if (!kpis) {
    return <EmptyState icon={<AlertTriangle size={48} className="text-warning" />} title="Unable to load KPIs" description="Could not retrieve platform analytics." />;
  }

  return (
    <div>
      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <KPICard label="Total Organizations" value={kpis.total_organizations} color="var(--color-primary)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Active Organizations" value={kpis.active_organizations} color="var(--color-success)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Total Users" value={kpis.total_users} color="var(--color-info)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Total Employees" value={kpis.total_employees} color="var(--color-warning)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Total Requests" value={kpis.total_requests} color="var(--color-danger)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Completion Rate" value={`${kpis.completion_rate?.toFixed(1)}%`} color="var(--color-success)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Avg Resolution Time" value={`${kpis.avg_resolution_time_hours?.toFixed(1)}h`} color="var(--color-warning)" />
        </div>
        <div className="col-6 col-md-3">
          <KPICard label="Overall Satisfaction" value={`${kpis.overall_satisfaction_rating?.toFixed(1)}/5`} color="var(--color-warning)" />
        </div>
      </div>

      {/* Platform Analytics Charts */}
      <div className="row g-4">
        {/* Requests by Organization */}
        {kpis.requests_by_organization && kpis.requests_by_organization.length > 0 && (
          <div className="col-12 col-xl-6">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
              <h6 className="fw-bold text-dark mb-3">Requests by Organization</h6>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={kpis.requests_by_organization}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                    <XAxis dataKey="organization_name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Total Requests" fill="#0d6efd" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Requests by Domain */}
        {kpis.requests_by_domain && kpis.requests_by_domain.length > 0 && (
          <div className="col-12 col-xl-6">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
              <h6 className="fw-bold text-dark mb-3">Requests by Domain</h6>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={kpis.requests_by_domain}
                      dataKey="count"
                      nameKey="domain"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label
                    >
                      {kpis.requests_by_domain.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={['#0d6efd', '#20c997', '#ffc107', '#fd7e14', '#d63384', '#6f42c1', '#0dcaf0', '#adb5bd'][index % 8]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Requests by Status */}
        {kpis.requests_by_status && kpis.requests_by_status.length > 0 && (
          <div className="col-12">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white">
              <h6 className="fw-bold text-dark mb-3">Request Status Distribution</h6>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={kpis.requests_by_status} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.3} />
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis dataKey="status" type="category" tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Count" fill="#0d6efd" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Organizations Section ───────────────────────────────────────────────────────────
const OrganizationsSection: React.FC<{ organizations: Organization[]; loading: boolean }> = ({ organizations, loading }) => {
  const [searchQuery, setSearchQuery] = useState('');

  if (loading) {
    return <SkeletonTable rows={6} />;
  }

    const filtered = organizations.filter((org) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return org.name.toLowerCase().includes(q) || org.org_type_display?.toLowerCase().includes(q) || org.org_type?.toLowerCase().includes(q);
  });

  if (filtered.length === 0) {
    return <EmptyState icon={<Building2 size={48} className="text-muted" />} title="No organizations found" description="No organizations match your search." />;
  }

  return (
    <div className="card border-0 shadow-sm rounded-3 bg-white p-4">
      <div className="mb-4">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light border-end-0">
            <Search size={14} className="text-muted" />
          </span>
          <input
            type="text"
            className="form-control border-start-0 bg-light"
            placeholder="Search by organization name or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="table-responsive">
        <table className="table table-hover align-middle mb-0 small">
          <thead className="table-light">
            <tr>
              <th>Organization Name</th>
              <th>Type</th>
              <th>Location</th>
              <th>Users</th>
              <th>Employees</th>
              <th>Active Requests</th>
              <th>Status</th>
              <th className="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((org) => (
              <tr key={org.id}>
                <td className="fw-bold text-dark">{org.name}</td>
                <td className="small text-muted">{org.org_type_display || org.org_type || 'N/A'}</td>
                <td className="small text-muted">{org.address || 'N/A'}</td>
                <td>
                  <span className="badge bg-info-subtle text-info border border-info-subtle">{(org as any).user_count ?? 0}</span>
                </td>
                <td>
                  <span className="badge bg-warning-subtle text-warning border border-warning-subtle">{(org as any).employee_count ?? 0}</span>
                </td>
                <td>
                  <span className="badge bg-danger-subtle text-danger border border-danger-subtle">{(org as any).active_request_count ?? 0}</span>
                </td>
                <td>
                  <span className={`badge ${org.is_active ? 'bg-success' : 'bg-secondary'}`}>
                    {org.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="text-end">
                  <button className="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-1 rounded-3">
                    <Eye size={13} />
                    <span>View</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Users Section ───────────────────────────────────────────────────────────
const UsersSection: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [activeFilter, setActiveFilter] = useState('ALL');

  return (
    <div className="card border-0 shadow-sm rounded-3 bg-white p-4">
      <div className="row g-3 align-items-center mb-4">
        <div className="col-12 col-md-5">
          <div className="input-group input-group-sm">
            <span className="input-group-text bg-light border-end-0">
              <Search size={14} className="text-muted" />
            </span>
            <input
              type="text"
              className="form-control border-start-0 bg-light"
              placeholder="Search by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="col-6 col-md-2">
          <select className="form-select form-select-sm" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="ALL">All Roles</option>
            <option value="USER">Resident</option>
            <option value="EMPLOYEE">Employee</option>
            <option value="ADMIN">Admin</option>
          </select>
        </div>

        <div className="col-6 col-md-2">
          <select className="form-select form-select-sm" value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)}>
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>

        <div className="col-12 col-md-3 text-end">
          <button className="btn btn-outline-secondary btn-sm w-100" onClick={() => { setSearchQuery(''); setRoleFilter('ALL'); setActiveFilter('ALL'); }}>
            Reset Filters
          </button>
        </div>
      </div>

      <div className="alert alert-info small py-2 px-3" role="alert">
        <strong>Note:</strong> User management for cross-organization administration would be implemented with real API endpoints and full CRUD operations.
      </div>
    </div>
  );
};

// ─── Main Super Admin Portal ───────────────────────────────────────────────────────
export const SuperAdminPortal: React.FC = () => {
  const [activeSection, setActiveSection] = useState<Section>('dashboard');
  const [kpis, setKpis] = useState<PlatformKPIs | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 size={16} /> },
    { id: 'organizations', label: 'Organizations', icon: <Building2 size={16} /> },
    { id: 'users', label: 'Users', icon: <Users size={16} /> },
    { id: 'analytics', label: 'Analytics', icon: <TrendingUp size={16} /> },
  ];

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiRes, orgRes] = await Promise.all([
        apiAnalytics.getPlatform(),
        apiOrganizations.list(),
      ]);
      setKpis(kpiRes);
      setOrganizations(orgRes);
    } catch (err) {
      console.error('Failed to load super admin data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="portal-layout">
      <Sidebar sections={navItems} activeSection={activeSection} onSelect={(id) => setActiveSection(id as Section)} />
      <div className="portal-content">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h5 className="fw-bold mb-1">{navItems.find((n) => n.id === activeSection)?.label}</h5>
            <p className="text-muted small mb-0">
              {activeSection === 'dashboard' ? 'Platform-wide metrics and cross-organization insights'
                : activeSection === 'organizations' ? 'Manage all organizations on the platform'
                : activeSection === 'users' ? 'Manage all users across organizations'
                : 'Detailed platform analytics and trends'}
            </p>
          </div>
          <button onClick={loadData} disabled={loading} className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1 rounded-3">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>

        {activeSection === 'dashboard' && <DashboardSection kpis={kpis} loading={loading} />}
        {activeSection === 'organizations' && <OrganizationsSection organizations={organizations} loading={loading} />}
        {activeSection === 'users' && <UsersSection />}
        {activeSection === 'analytics' && (
          <EmptyState
            icon={<BarChart3 size={48} className="text-muted" />}
            title="Analytics Page"
            description="Detailed cross-organization analytics and reporting would be implemented here with additional chart types and filtering capabilities."
          />
        )}
      </div>
    </div>
  );
};
