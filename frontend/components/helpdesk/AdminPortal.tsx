'use client';

import React, { useState, useEffect } from 'react';
import {
  OverviewKPIs,
  ChartsData,
  ServiceRequest,
  Employee,
  ServiceDomain,
} from '@/lib/types';
import {
  apiAnalytics,
  apiRequests,
  apiEmployees,
  apiServices,
} from '@/lib/api';
import {
  Activity,
  Layers,
  Users,
  CheckCircle2,
  Clock,
  Star,
  AlertTriangle,
  Flame,
  Search,
  Filter,
  Eye,
  RefreshCw,
  Plus,
  Zap,
  Droplets,
  Fan,
  Hammer,
  Sparkles,
  Shield,
  Wifi,
  Wrench,
  ChevronRight,
  TrendingUp,
  Award,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

interface AdminPortalProps {
  onInspectRequest: (requestId: string) => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  LOW: '#6c757d',
  NORMAL: '#0d6efd',
  HIGH: '#fd7e14',
  URGENT: '#dc3545',
  CRITICAL: '#6f42c1',
};

const CHART_COLORS = ['#0d6efd', '#20c997', '#ffc107', '#fd7e14', '#d63384', '#6f42c1', '#0dcaf0', '#adb5bd'];

export const AdminPortal: React.FC<AdminPortalProps> = ({ onInspectRequest }) => {
  const [activeTab, setActiveTab] = useState<'analytics' | 'requests' | 'workforce' | 'domains'>('analytics');
  const [kpis, setKpis] = useState<OverviewKPIs | null>(null);
  const [charts, setCharts] = useState<ChartsData | null>(null);
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [domains, setDomains] = useState<ServiceDomain[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDomain, setSelectedDomain] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL');

  // Workforce Filters & Sort
  const [empSearch, setEmpSearch] = useState<string>('');
  const [empAvailFilter, setEmpAvailFilter] = useState<'ALL' | 'AVAILABLE' | 'UNAVAILABLE'>('ALL');
  const [empStatusFilter, setEmpStatusFilter] = useState<string>('ALL');
  const [empSortField, setEmpSortField] = useState<'name' | 'workload' | 'rating' | 'completed'>('name');
  const [selectedEmployeeDetail, setSelectedEmployeeDetail] = useState<Employee | null>(null);

  // New domain form
  const [showDomainModal, setShowDomainModal] = useState<boolean>(false);
  const [newDomainName, setNewDomainName] = useState<string>('');
  const [newDomainSla, setNewDomainSla] = useState<number>(12);
  const [newDomainDesc, setNewDomainDesc] = useState<string>('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiRes, chartRes, reqRes, empRes, domRes] = await Promise.all([
        apiAnalytics.getOverview(),
        apiAnalytics.getCharts(14),
        apiRequests.list(),
        apiEmployees.list(),
        apiServices.listDomains(),
      ]);
      setKpis(kpiRes);
      setCharts(chartRes);
      setRequests(reqRes);
      setEmployees(empRes);
      setDomains(domRes);
    } catch (err) {
      console.error('Failed to load admin data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleAvailability = async (empId: string, current: boolean) => {
    try {
      await apiEmployees.toggleAvailability(empId, !current);
      setEmployees((prev) =>
        prev.map((e) => (e.id === empId ? { ...e, is_available: !current } : e))
      );
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDomainName.trim()) return;
    try {
      await apiServices.createDomain({
        name: newDomainName,
        sla_hours: newDomainSla,
        description: newDomainDesc,
      });
      setShowDomainModal(false);
      setNewDomainName('');
      setNewDomainDesc('');
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (selectedDomain !== 'ALL' && r.domain_details?.name !== selectedDomain) return false;
    if (selectedStatus !== 'ALL' && r.status !== selectedStatus) return false;
    if (selectedPriority !== 'ALL' && r.priority !== selectedPriority) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchDesc = r.custom_description.toLowerCase().includes(q);
      const matchUser = (r.user_details?.username || '').toLowerCase().includes(q);
      const matchLoc = r.location_name.toLowerCase().includes(q);
      const matchTech = (r.active_assignment?.employee_name || '').toLowerCase().includes(q);
      if (!matchDesc && !matchUser && !matchLoc && !matchTech) return false;
    }
    return true;
  });

  return (
    <div className="container-fluid py-4 px-3 px-lg-4">
      {/* Top Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
          <h4 className="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
            <span>Operations & Workforce Management</span>
            <span className="badge bg-primary-subtle text-primary border border-primary-subtle fs-6">
              Admin Portal
            </span>
          </h4>
          <p className="text-muted small mb-0">
            Real-time ticket lifecycle tracking, automated workforce assignments, and SLA analytics
          </p>
        </div>

        <div className="d-flex align-items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1 rounded-3"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowDomainModal(true)}
            className="btn btn-primary btn-sm d-flex align-items-center gap-1 rounded-3"
          >
            <Plus size={15} />
            <span>New Service Domain</span>
          </button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      {kpis && (
        <div className="row g-3 mb-4">
          <div className="col-6 col-md-4 col-xl-2">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
              <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                <span>Total Requests</span>
                <Layers size={16} className="text-primary" />
              </div>
              <div className="fs-3 fw-bold text-dark">{kpis.total_requests}</div>
              <div className="text-success small mt-auto fw-medium">All logged tickets</div>
            </div>
          </div>

          <div className="col-6 col-md-4 col-xl-2">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
              <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                <span>Active / In Progress</span>
                <Activity size={16} className="text-warning" />
              </div>
              <div className="fs-3 fw-bold text-warning">{kpis.open_requests}</div>
              <div className="text-muted small mt-auto">
                {kpis.in_progress_requests} currently in-field
              </div>
            </div>
          </div>

          <div className="col-6 col-md-4 col-xl-2">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
              <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                <span>Urgent & Critical</span>
                <Flame size={16} className="text-danger" />
              </div>
              <div className="fs-3 fw-bold text-danger">
                {kpis.urgent_requests + kpis.critical_requests}
              </div>
              <div className="text-danger small mt-auto fw-medium">High priority queue</div>
            </div>
          </div>

          <div className="col-6 col-md-4 col-xl-2">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
              <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                <span>SLA Compliance</span>
                <Clock size={16} className="text-success" />
              </div>
              <div className="fs-3 fw-bold text-success">{kpis.sla_compliance_rate}%</div>
              <div className="text-muted small mt-auto">Within domain targets</div>
            </div>
          </div>

          <div className="col-6 col-md-4 col-xl-2">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
              <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                <span>Customer Rating</span>
                <Star size={16} className="text-warning fill-warning" />
              </div>
              <div className="fs-3 fw-bold text-dark">{kpis.avg_rating} <small className="fs-6 text-muted">/ 5.0</small></div>
              <div className="text-muted small mt-auto">Post-resolution feedback</div>
            </div>
          </div>

          <div className="col-6 col-md-4 col-xl-2">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
              <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                <span>Workforce Active</span>
                <Users size={16} className="text-info" />
              </div>
              <div className="fs-3 fw-bold text-info">
                {kpis.available_employees} <small className="fs-6 text-muted">/ {kpis.total_employees}</small>
              </div>
              <div className="text-muted small mt-auto">Staff on duty</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Tabs Navigation */}
      <ul className="nav nav-pills bg-white p-2 rounded-3 shadow-sm mb-4 border">
        <li className="nav-item">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`nav-link py-2 px-3 fw-semibold ${
              activeTab === 'analytics' ? 'active shadow-sm' : 'text-secondary'
            }`}
          >
            <TrendingUp size={16} className="me-2 d-inline" />
            Analytics & Insights
          </button>
        </li>
        <li className="nav-item">
          <button
            onClick={() => setActiveTab('requests')}
            className={`nav-link py-2 px-3 fw-semibold ${
              activeTab === 'requests' ? 'active shadow-sm' : 'text-secondary'
            }`}
          >
            <Layers size={16} className="me-2 d-inline" />
            Service Requests ({requests.length})
          </button>
        </li>
        <li className="nav-item">
          <button
            onClick={() => setActiveTab('workforce')}
            className={`nav-link py-2 px-3 fw-semibold ${
              activeTab === 'workforce' ? 'active shadow-sm' : 'text-secondary'
            }`}
          >
            <Users size={16} className="me-2 d-inline" />
            Workforce & Skills ({employees.length})
          </button>
        </li>
        <li className="nav-item">
          <button
            onClick={() => setActiveTab('domains')}
            className={`nav-link py-2 px-3 fw-semibold ${
              activeTab === 'domains' ? 'active shadow-sm' : 'text-secondary'
            }`}
          >
            <Wrench size={16} className="me-2 d-inline" />
            Service Domains & SLAs ({domains.length})
          </button>
        </li>
      </ul>

      {/* TAB 1: ANALYTICS & INSIGHTS */}
      {activeTab === 'analytics' && charts && (
        <div className="row g-4">
          {/* Chart 1: Volume Over Time */}
          <div className="col-12 col-xl-8">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
              <h6 className="fw-bold text-dark mb-1">Request Volume Over Time</h6>
              <p className="text-muted small mb-3">Daily inflow of created vs. completed service tickets</p>
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <AreaChart data={charts.daily_trend}>
                    <defs>
                      <linearGradient id="createdGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0d6efd" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#0d6efd" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="completedGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#20c997" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#20c997" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="created" name="Tickets Raised" stroke="#0d6efd" fillOpacity={1} fill="url(#createdGrad)" />
                    <Area type="monotone" dataKey="completed" name="Tickets Resolved" stroke="#20c997" fillOpacity={1} fill="url(#completedGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Chart 2: Priority Distribution */}
          <div className="col-12 col-md-6 col-xl-4">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
              <h6 className="fw-bold text-dark mb-1">Tickets by Priority</h6>
              <p className="text-muted small mb-3">Distribution of workload urgency</p>
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={charts.by_priority}
                      dataKey="count"
                      nameKey="priority"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={95}
                      paddingAngle={3}
                    >
                      {charts.by_priority.map((entry) => (
                        <Cell
                          key={entry.priority}
                          fill={PRIORITY_COLORS[entry.priority] || '#6c757d'}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Chart 3: Requests by Domain */}
          <div className="col-12 col-md-6 col-xl-6">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
              <h6 className="fw-bold text-dark mb-1">Requests by Service Domain</h6>
              <p className="text-muted small mb-3">Volume comparison across trades</p>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={charts.by_domain}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                    <XAxis dataKey="domain" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Total Requests" fill="#0d6efd" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="completed" name="Completed" fill="#20c997" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Chart 4: User Satisfaction Ratings */}
          <div className="col-12 col-md-6 col-xl-6">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
              <h6 className="fw-bold text-dark mb-1">Customer Satisfaction Breakdown</h6>
              <p className="text-muted small mb-3">Feedback star distribution from verified resolutions</p>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={charts.satisfaction_breakdown} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.3} />
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis dataKey="stars" type="category" tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Reviews" fill="#ffc107" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Employee Performance Matrix */}
          <div className="col-12">
            <div className="card border-0 shadow-sm rounded-3 p-4 bg-white">
              <h6 className="fw-bold text-dark mb-3 d-flex align-items-center gap-2">
                <Award size={18} className="text-primary" />
                <span>Workforce Performance & SLA Compliance Scorecard</span>
              </h6>
              <div className="table-responsive">
                <table className="table table-hover align-middle mb-0 small">
                  <thead className="table-light">
                    <tr>
                      <th>Staff Member</th>
                      <th>Trade Role</th>
                      <th>Status & Availability</th>
                      <th>Current Workload</th>
                      <th>Completed Jobs</th>
                      <th>Customer Rating</th>
                      <th>SLA Compliance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {charts.workforce_performance.map((emp) => (
                      <tr key={emp.id}>
                        <td className="fw-bold text-dark">{emp.name}</td>
                        <td>{emp.role}</td>
                        <td>
                          {emp.is_available && emp.status === 'ACTIVE' ? (
                            <span className="badge bg-success-subtle text-success border border-success-subtle">
                              On Duty / Available
                            </span>
                          ) : (
                            <span className="badge bg-secondary-subtle text-secondary border">
                              {emp.status}
                            </span>
                          )}
                        </td>
                        <td>
                          <div className="d-flex align-items-center gap-2">
                            <div className="progress flex-grow-1" style={{ height: 6 }}>
                              <div
                                className={`progress-bar ${
                                  emp.workload_pct >= 100
                                    ? 'bg-danger'
                                    : emp.workload_pct >= 60
                                    ? 'bg-warning'
                                    : 'bg-primary'
                                }`}
                                style={{ width: `${Math.min(100, emp.workload_pct)}%` }}
                              />
                            </div>
                            <span className="fw-semibold">
                              {emp.current_active} / {emp.max_capacity}
                            </span>
                          </div>
                        </td>
                        <td className="fw-semibold">{emp.completed_total}</td>
                        <td className="fw-semibold text-warning">
                          ⭐ {emp.avg_rating.toFixed(1)} / 5.0
                        </td>
                        <td>
                          <span
                            className={`badge ${
                              emp.sla_compliance_pct >= 90
                                ? 'bg-success'
                                : emp.sla_compliance_pct >= 70
                                ? 'bg-warning text-dark'
                                : 'bg-danger'
                            }`}
                          >
                            {emp.sla_compliance_pct}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SERVICE REQUESTS STREAM */}
      {activeTab === 'requests' && (
        <div className="card border-0 shadow-sm rounded-3 bg-white p-4">
          {/* Filter Bar */}
          <div className="row g-3 align-items-center mb-4">
            <div className="col-12 col-md-4">
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light border-end-0">
                  <Search size={14} className="text-muted" />
                </span>
                <input
                  type="text"
                  className="form-control border-start-0 bg-light"
                  placeholder="Search by description, location, resident, tech..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="col-6 col-md-3">
              <select
                className="form-select form-select-sm"
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
              >
                <option value="ALL">All Domains</option>
                {domains.map((d) => (
                  <option key={d.id} value={d.name}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-6 col-md-2">
              <select
                className="form-select form-select-sm"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="CREATED">Created</option>
                <option value="QUEUED">Queued</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
                <option value="REOPENED">Reopened</option>
              </select>
            </div>

            <div className="col-6 col-md-2">
              <select
                className="form-select form-select-sm"
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
              >
                <option value="ALL">All Priorities</option>
                <option value="LOW">Low</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>

            <div className="col-6 col-md-1 text-end">
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedDomain('ALL');
                  setSelectedStatus('ALL');
                  setSelectedPriority('ALL');
                }}
                className="btn btn-outline-secondary btn-sm w-100"
                title="Reset Filters"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0 small">
              <thead className="table-light">
                <tr>
                  <th>Request ID</th>
                  <th>Domain & Issue</th>
                  <th>Requester & Location</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Assigned Workforce & Proximity</th>
                  <th>Ranking Score</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequests.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-5 text-muted">
                      No service requests match the current filters.
                    </td>
                  </tr>
                ) : (
                  filteredRequests.map((req) => {
                    const assign = req.active_assignment;
                    return (
                      <tr key={req.id}>
                        <td className="fw-mono text-muted" style={{ fontSize: '0.75rem' }}>
                          #{req.id.slice(0, 8)}
                        </td>
                        <td>
                          <div className="fw-bold text-dark">
                            {req.domain_details?.name || 'Trade Request'}
                          </div>
                          <div className="text-muted text-truncate" style={{ maxWidth: 220 }}>
                            {req.predefined_issue_details?.title || req.custom_description}
                          </div>
                        </td>
                        <td>
                          <div className="fw-semibold text-dark">
                            {req.user_details?.first_name
                              ? `${req.user_details.first_name} ${req.user_details.last_name}`
                              : req.user_details?.username}
                          </div>
                          <div className="text-muted small">{req.location_name || 'Unit location'}</div>
                        </td>
                        <td>
                          <span
                            className="badge"
                            style={{
                              backgroundColor: `${PRIORITY_COLORS[req.priority]}22`,
                              color: PRIORITY_COLORS[req.priority],
                              border: `1px solid ${PRIORITY_COLORS[req.priority]}55`,
                            }}
                          >
                            {req.priority_display || req.priority}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`badge ${
                              req.status === 'COMPLETED'
                                ? 'bg-success'
                                : req.status === 'IN_PROGRESS'
                                ? 'bg-warning text-dark'
                                : req.status === 'ASSIGNED'
                                ? 'bg-primary'
                                : req.status === 'REOPENED'
                                ? 'bg-danger'
                                : 'bg-secondary'
                            }`}
                          >
                            {req.status_display || req.status}
                          </span>
                        </td>
                        <td>
                          {assign ? (
                            <div>
                              <div className="fw-bold text-dark">{assign.employee_name}</div>
                              <div className="text-danger small fw-semibold">
                                📍 {assign.distance_km.toFixed(2)} km away
                              </div>
                            </div>
                          ) : (
                            <span className="badge bg-secondary-subtle text-secondary">
                              Unassigned / Queued
                            </span>
                          )}
                        </td>
                        <td>
                          {assign?.suitability_score ? (
                            <div>
                              <span className="fw-bold text-primary">
                                {(assign.suitability_score * 100).toFixed(1)}%
                              </span>
                              <div className="text-muted" style={{ fontSize: '0.68rem' }}>
                                {assign.ranking_model_version}
                              </div>
                            </div>
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>
                        <td className="text-end">
                          <button
                            onClick={() => onInspectRequest(req.id)}
                            className="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-1 rounded-3"
                            title="Inspect candidate ranking scores and features"
                          >
                            <Eye size={13} />
                            <span>Inspect</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: WORKFORCE DIRECTORY & MANAGEMENT */}
      {activeTab === 'workforce' && (
        <div className="d-flex flex-column gap-4">
          {/* Workforce Specific KPIs */}
          <div className="row g-3">
            <div className="col-12 col-sm-6 col-lg">
              <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
                <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                  <span>Total Employees</span>
                  <Users size={16} className="text-primary" />
                </div>
                <div className="fs-3 fw-bold text-dark">{kpis?.total_employees ?? employees.length}</div>
                <div className="text-muted small">Registered staff</div>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg">
              <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
                <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                  <span>Available Employees</span>
                  <CheckCircle2 size={16} className="text-success" />
                </div>
                <div className="fs-3 fw-bold text-success">
                  {kpis?.available_employees ?? employees.filter(e => e.is_available && e.status === 'ACTIVE').length}
                </div>
                <div className="text-success small fw-medium">Ready for assignment</div>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg">
              <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
                <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                  <span>Unavailable Employees</span>
                  <Clock size={16} className="text-secondary" />
                </div>
                <div className="fs-3 fw-bold text-secondary">
                  {kpis?.unavailable_employees ?? (
                    (kpis?.total_employees ?? employees.length) - (kpis?.available_employees ?? employees.filter(e => e.is_available && e.status === 'ACTIVE').length)
                  )}
                </div>
                <div className="text-muted small">Off duty / On leave</div>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg">
              <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
                <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                  <span>Active Requests</span>
                  <Activity size={16} className="text-warning" />
                </div>
                <div className="fs-3 fw-bold text-warning">
                  {kpis?.active_requests ?? kpis?.in_progress_requests ?? requests.filter(r => r.status === 'IN_PROGRESS').length}
                </div>
                <div className="text-muted small">In-field execution</div>
              </div>
            </div>

            <div className="col-12 col-sm-6 col-lg">
              <div className="card border-0 shadow-sm rounded-3 p-3 bg-white h-100">
                <div className="d-flex justify-content-between align-items-center text-muted small mb-1">
                  <span>Employees at Capacity</span>
                  <AlertTriangle size={16} className="text-danger" />
                </div>
                <div className="fs-3 fw-bold text-danger">
                  {kpis?.employees_at_capacity ?? employees.filter(e => e.active_assignments_count >= e.max_active_assignments).length}
                </div>
                <div className="text-danger small fw-medium">Max active workload</div>
              </div>
            </div>
          </div>

          {/* Workforce Table & Filter Controls */}
          <div className="card border-0 shadow-sm rounded-3 bg-white p-4">
            <div className="row g-3 align-items-center mb-4">
              <div className="col-12 col-md-4">
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light border-end-0">
                    <Search size={14} className="text-muted" />
                  </span>
                  <input
                    type="text"
                    className="form-control border-start-0 bg-light"
                    placeholder="Search by name, role, skill..."
                    value={empSearch}
                    onChange={(e) => setEmpSearch(e.target.value)}
                  />
                </div>
              </div>

              <div className="col-6 col-md-2">
                <select
                  className="form-select form-select-sm"
                  value={empAvailFilter}
                  onChange={(e) => setEmpAvailFilter(e.target.value as any)}
                >
                  <option value="ALL">All Availability</option>
                  <option value="AVAILABLE">Available</option>
                  <option value="UNAVAILABLE">Unavailable</option>
                </select>
              </div>

              <div className="col-6 col-md-2">
                <select
                  className="form-select form-select-sm"
                  value={empStatusFilter}
                  onChange={(e) => setEmpStatusFilter(e.target.value)}
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">Active / On Duty</option>
                  <option value="ON_LEAVE">On Leave</option>
                  <option value="OFF_DUTY">Off Duty</option>
                  <option value="INACTIVE">Inactive</option>
                </select>
              </div>

              <div className="col-6 col-md-2">
                <select
                  className="form-select form-select-sm"
                  value={empSortField}
                  onChange={(e) => setEmpSortField(e.target.value as any)}
                >
                  <option value="name">Sort by Name</option>
                  <option value="workload">Sort by Workload %</option>
                  <option value="rating">Sort by Rating</option>
                  <option value="completed">Sort by Completed</option>
                </select>
              </div>

              <div className="col-6 col-md-2 text-end">
                <button
                  onClick={() => {
                    setEmpSearch('');
                    setEmpAvailFilter('ALL');
                    setEmpStatusFilter('ALL');
                    setEmpSortField('name');
                  }}
                  className="btn btn-outline-secondary btn-sm w-100"
                >
                  Reset Filters
                </button>
              </div>
            </div>

            {/* Workforce Table */}
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0 small">
                <thead className="table-light">
                  <tr>
                    <th>Employee</th>
                    <th>Role</th>
                    <th>Certified Skills</th>
                    <th>Availability</th>
                    <th>Current Workload</th>
                    <th>Rating</th>
                    <th>Completion Rate</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    const filteredEmps = employees
                      .filter((emp) => {
                        if (empAvailFilter === 'AVAILABLE' && (!emp.is_available || emp.status !== 'ACTIVE')) return false;
                        if (empAvailFilter === 'UNAVAILABLE' && emp.is_available && emp.status === 'ACTIVE') return false;
                        if (empStatusFilter !== 'ALL' && emp.status !== empStatusFilter) return false;
                        if (empSearch) {
                          const q = empSearch.toLowerCase();
                          const nameMatch = (emp.user_details?.first_name ? `${emp.user_details.first_name} ${emp.user_details.last_name}` : emp.user_details?.username || '').toLowerCase().includes(q);
                          const roleMatch = (emp.role_details?.title || '').toLowerCase().includes(q);
                          const skillMatch = emp.skills.some((s) => s.domain_name.toLowerCase().includes(q));
                          if (!nameMatch && !roleMatch && !skillMatch) return false;
                        }
                        return true;
                      })
                      .sort((a, b) => {
                        if (empSortField === 'workload') {
                          const pctA = a.active_assignments_count / Math.max(1, a.max_active_assignments);
                          const pctB = b.active_assignments_count / Math.max(1, b.max_active_assignments);
                          return pctB - pctA;
                        }
                        if (empSortField === 'rating') return b.historical_avg_rating - a.historical_avg_rating;
                        if (empSortField === 'completed') return b.historical_completed_count - a.historical_completed_count;
                        const nameA = a.user_details?.first_name || a.user_details?.username || '';
                        const nameB = b.user_details?.first_name || b.user_details?.username || '';
                        return nameA.localeCompare(nameB);
                      });

                    if (filteredEmps.length === 0) {
                      return (
                        <tr>
                          <td colSpan={8} className="text-center py-5 text-muted">
                            No employees match the current filter criteria.
                          </td>
                        </tr>
                      );
                    }

                    return filteredEmps.map((emp) => {
                      const perfData = charts?.workforce_performance?.find((wp) => wp.id === emp.id);
                      const compRate = perfData?.completion_rate ?? (
                        emp.historical_completed_count > 0
                          ? Math.round((emp.historical_completed_count / (emp.historical_completed_count + emp.active_assignments_count)) * 100)
                          : 100
                      );

                      return (
                        <tr key={emp.id}>
                          <td>
                            <div className="fw-bold text-dark">
                              {emp.user_details?.first_name
                                ? `${emp.user_details.first_name} ${emp.user_details.last_name}`
                                : emp.user_details?.username}
                            </div>
                            <div className="text-muted small">{emp.user_details?.email}</div>
                          </td>
                          <td>
                            <span className="fw-semibold text-secondary">
                              {emp.role_details?.title || 'Staff Technician'}
                            </span>
                          </td>
                          <td>
                            <div className="d-flex flex-wrap gap-1" style={{ maxWidth: 240 }}>
                              {emp.skills.map((s) => (
                                <span key={s.id} className="badge bg-light text-dark border">
                                  {s.domain_name} (Lvl {s.proficiency_level})
                                </span>
                              ))}
                            </div>
                          </td>
                          <td>
                            <div className="d-flex align-items-center gap-2">
                              <div className="form-check form-switch m-0">
                                <input
                                  className="form-check-input"
                                  type="checkbox"
                                  role="switch"
                                  checked={emp.is_available}
                                  onChange={() => handleToggleAvailability(emp.id, emp.is_available)}
                                  title="Toggle availability"
                                />
                              </div>
                              <span
                                className={`badge ${
                                  emp.status === 'ACTIVE' && emp.is_available
                                    ? 'bg-success'
                                    : emp.status === 'ON_LEAVE'
                                    ? 'bg-warning text-dark'
                                    : 'bg-secondary'
                                }`}
                              >
                                {emp.is_available && emp.status === 'ACTIVE' ? 'Available' : emp.status_display}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div className="d-flex align-items-center gap-2" style={{ width: 140 }}>
                              <div className="progress flex-grow-1" style={{ height: 6 }}>
                                <div
                                  className={`progress-bar ${
                                    emp.active_assignments_count >= emp.max_active_assignments
                                      ? 'bg-danger'
                                      : emp.active_assignments_count > 0
                                      ? 'bg-primary'
                                      : 'bg-secondary'
                                  }`}
                                  style={{
                                    width: `${Math.min(100, (emp.active_assignments_count / Math.max(1, emp.max_active_assignments)) * 100)}%`,
                                  }}
                                />
                              </div>
                              <span className="fw-semibold">
                                {emp.active_assignments_count} / {emp.max_active_assignments}
                              </span>
                            </div>
                          </td>
                          <td className="fw-semibold text-warning">
                            ⭐ {emp.historical_avg_rating.toFixed(1)}
                          </td>
                          <td>
                            <span className="badge bg-info-subtle text-info border border-info-subtle fw-semibold">
                              {compRate}%
                            </span>
                          </td>
                          <td className="text-end">
                            <button
                              onClick={() => setSelectedEmployeeDetail(emp)}
                              className="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-1 rounded-3"
                            >
                              <Eye size={13} />
                              <span>View Details</span>
                            </button>
                          </td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: SERVICE DOMAINS & SLAS */}
      {activeTab === 'domains' && (
        <div className="row g-4">
          {domains.map((dom) => (
            <div key={dom.id} className="col-12 col-md-6 col-xl-4">
              <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <div className="d-flex align-items-center gap-2">
                    <div className="bg-primary text-white p-2 rounded-3">
                      <Wrench size={18} />
                    </div>
                    <div>
                      <h6 className="fw-bold text-dark mb-0">{dom.name}</h6>
                      <small className="text-muted">Target SLA: {dom.sla_hours} Hours</small>
                    </div>
                  </div>
                  <span className="badge bg-info-subtle text-info border">
                    {dom.employee_count || 0} Staff
                  </span>
                </div>

                <p className="text-secondary small mb-3">{dom.description}</p>

                <div className="mb-3">
                  <small className="fw-semibold text-muted d-block mb-2">Predefined Common Issues:</small>
                  <ul className="list-unstyled mb-0 small">
                    {dom.predefined_issues && dom.predefined_issues.length > 0 ? (
                      dom.predefined_issues.map((iss) => (
                        <li key={iss.id} className="d-flex justify-content-between align-items-center py-1 border-bottom border-light">
                          <span>{iss.title}</span>
                          <span
                            className="badge py-0"
                            style={{
                              backgroundColor: `${PRIORITY_COLORS[iss.default_priority]}15`,
                              color: PRIORITY_COLORS[iss.default_priority],
                            }}
                          >
                            {iss.default_priority}
                          </span>
                        </li>
                      ))
                    ) : (
                      <li className="text-muted">No predefined issues configured.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Service Domain Modal */}
      {showDomainModal && (
        <div
          className="modal show d-block"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}
          tabIndex={-1}
        >
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content border-0 shadow-lg rounded-4">
              <div className="modal-header bg-primary text-white border-0 py-3 px-4 rounded-top-4">
                <h5 className="modal-title fw-bold">Configure New Service Domain</h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setShowDomainModal(false)}
                />
              </div>
              <form onSubmit={handleCreateDomain}>
                <div className="modal-body p-4">
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Domain Name:</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Solar Inverter & Battery Maintenance"
                      value={newDomainName}
                      onChange={(e) => setNewDomainName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Target SLA Target (Hours):</label>
                    <input
                      type="number"
                      className="form-control"
                      min={1}
                      max={168}
                      value={newDomainSla}
                      onChange={(e) => setNewDomainSla(Number(e.target.value))}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Description:</label>
                    <textarea
                      className="form-control"
                      rows={3}
                      placeholder="Scope of work, special tools required, safety guidelines..."
                      value={newDomainDesc}
                      onChange={(e) => setNewDomainDesc(e.target.value)}
                    />
                  </div>
                </div>
                <div className="modal-footer border-0 bg-light px-4 py-3 rounded-bottom-4">
                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={() => setShowDomainModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary px-4 fw-semibold">
                    Create Domain
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Employee Detail Modal */}
      {selectedEmployeeDetail && (
        <div
          className="modal show d-block"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}
          tabIndex={-1}
        >
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content border-0 shadow-lg rounded-4">
              <div className="modal-header bg-dark text-white border-0 py-3 px-4 rounded-top-4">
                <div className="d-flex align-items-center gap-3">
                  <div className="bg-primary text-white p-2 rounded-circle">
                    <Users size={20} />
                  </div>
                  <div>
                    <h5 className="modal-title fw-bold mb-0">
                      {selectedEmployeeDetail.user_details?.first_name
                        ? `${selectedEmployeeDetail.user_details.first_name} ${selectedEmployeeDetail.user_details.last_name}`
                        : selectedEmployeeDetail.user_details?.username}
                    </h5>
                    <small className="text-light opacity-75">
                      {selectedEmployeeDetail.role_details?.title || 'Staff Member'} &bull; {selectedEmployeeDetail.user_details?.email}
                    </small>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setSelectedEmployeeDetail(null)}
                />
              </div>

              <div className="modal-body p-4">
                {/* Employee Overview Cards */}
                <div className="row g-3 mb-4">
                  <div className="col-6 col-md-3">
                    <div className="p-3 bg-light rounded-3 border">
                      <small className="text-muted d-block mb-1">Status & Duty</small>
                      <span className={`badge ${selectedEmployeeDetail.status === 'ACTIVE' && selectedEmployeeDetail.is_available ? 'bg-success' : 'bg-secondary'}`}>
                        {selectedEmployeeDetail.is_available && selectedEmployeeDetail.status === 'ACTIVE' ? 'Available / On Duty' : selectedEmployeeDetail.status_display}
                      </span>
                    </div>
                  </div>

                  <div className="col-6 col-md-3">
                    <div className="p-3 bg-light rounded-3 border">
                      <small className="text-muted d-block mb-1">Experience</small>
                      <strong className="fs-6 text-dark">{selectedEmployeeDetail.experience_years} Years</strong>
                    </div>
                  </div>

                  <div className="col-6 col-md-3">
                    <div className="p-3 bg-light rounded-3 border">
                      <small className="text-muted d-block mb-1">Active Workload</small>
                      <strong className="fs-6 text-primary">
                        {selectedEmployeeDetail.active_assignments_count} / {selectedEmployeeDetail.max_active_assignments} Jobs
                      </strong>
                    </div>
                  </div>

                  <div className="col-6 col-md-3">
                    <div className="p-3 bg-light rounded-3 border">
                      <small className="text-muted d-block mb-1">Average Rating</small>
                      <strong className="fs-6 text-warning">
                        ⭐ {selectedEmployeeDetail.historical_avg_rating.toFixed(1)} / 5.0
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Certified Skills & Proficiency */}
                <div className="mb-4">
                  <h6 className="fw-bold text-dark mb-2 d-flex align-items-center gap-2">
                    <Award size={16} className="text-primary" />
                    <span>Certified Service Skills & Proficiency</span>
                  </h6>
                  {selectedEmployeeDetail.skills && selectedEmployeeDetail.skills.length > 0 ? (
                    <div className="table-responsive">
                      <table className="table table-sm table-bordered align-middle mb-0 small">
                        <thead className="table-light">
                          <tr>
                            <th>Service Domain</th>
                            <th>Proficiency Level</th>
                            <th>Experience</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedEmployeeDetail.skills.map((sk) => {
                            const labels = ['', '1 - Beginner', '2 - Basic', '3 - Intermediate', '4 - Advanced', '5 - Expert'];
                            return (
                              <tr key={sk.id}>
                                <td className="fw-semibold text-dark">{sk.domain_name}</td>
                                <td>
                                  <span className="badge bg-primary-subtle text-primary border border-primary-subtle">
                                    {labels[sk.proficiency_level] || `Level ${sk.proficiency_level}`}
                                  </span>
                                </td>
                                <td>{sk.years_of_experience} yrs</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-muted small mb-0">No specific skills listed for this employee.</p>
                  )}
                </div>

                {/* Working Schedules */}
                <div className="mb-3">
                  <h6 className="fw-bold text-dark mb-2 d-flex align-items-center gap-2">
                    <Clock size={16} className="text-primary" />
                    <span>Working Schedule</span>
                  </h6>
                  {selectedEmployeeDetail.schedules && selectedEmployeeDetail.schedules.length > 0 ? (
                    <div className="table-responsive">
                      <table className="table table-sm table-bordered align-middle mb-0 small">
                        <thead className="table-light">
                          <tr>
                            <th>Day</th>
                            <th>Hours</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedEmployeeDetail.schedules.map((sch) => (
                            <tr key={sch.id}>
                              <td className="fw-semibold text-dark">{sch.day_name}</td>
                              <td>{sch.start_time} - {sch.end_time}</td>
                              <td>
                                {sch.is_active ? (
                                  <span className="badge bg-success-subtle text-success border border-success-subtle">Active</span>
                                ) : (
                                  <span className="badge bg-secondary-subtle text-secondary">Inactive</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-muted small mb-0">Standard operational schedule applies (Mon - Sat, 09:00 - 18:00).</p>
                  )}
                </div>
              </div>

              <div className="modal-footer border-0 bg-light px-4 py-3 rounded-bottom-4">
                <button
                  type="button"
                  className="btn btn-secondary px-4 fw-semibold"
                  onClick={() => setSelectedEmployeeDetail(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
