'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { apiRequests, apiEmployees } from '@/lib/api';
import { ServiceRequest, Employee } from '@/lib/types';
import { getPriorityColors, getStatusColors } from '@/lib/colors';
import { Sidebar } from './ui/Sidebar';
import { KPICard } from './ui/KPICard';
import { EmptyState } from './ui/EmptyState';
import { SkeletonCard, SkeletonTable } from './ui/SkeletonLoader';
import { LayoutDashboard, ClipboardList, History, User, MapPin, Phone, AlertTriangle, Clock, Star, CheckCircle, Play } from 'lucide-react';

type Section = 'dashboard' | 'tasks' | 'history' | 'profile';

// ─── Assignment Card ───────────────────────────────────────────────────────────
const EmpAssignmentCard: React.FC<{ request: ServiceRequest; onAction: (id: string, action: 'start' | 'complete') => void; loading: boolean }> = ({ request, onAction, loading }) => {
  const pc = getPriorityColors(request.priority);
  const isUrgent = request.priority === 'URGENT' || request.priority === 'CRITICAL';
  const title = request.predefined_issue_details?.title || request.custom_description?.substring(0, 60) || 'Service Request';
  return (
    <div className="request-card mb-3" style={isUrgent ? { borderLeft: '3px solid var(--color-danger)' } : {}}>
      <div className="d-flex align-items-center gap-2 mb-2 flex-wrap">
        {isUrgent && <AlertTriangle size={14} className="text-danger" />}
        <span className="badge rounded-pill" style={{ backgroundColor: pc.bg, color: pc.text, fontSize: '0.7rem' }}>{request.priority_display || request.priority}</span>
        <span className="text-muted small ms-auto">{request.domain_details?.name}</span>
      </div>
      <p className="fw-semibold small text-dark mb-2">{title}</p>
      {request.details_snapshot && Object.keys(request.details_snapshot).length > 0 && (
        <div className="small text-muted mb-2">
          {Object.entries(request.details_snapshot).filter(([, value]) => value !== '' && value !== false).slice(0, 3).map(([key, value]) => (
            <span className="badge text-bg-light me-1" key={key}>{key.replaceAll('_', ' ')}: {String(value)}</span>
          ))}
        </div>
      )}
      <div className="d-flex flex-wrap gap-3 text-muted mb-3" style={{ fontSize: '0.75rem' }}>
        {request.location_name && <span className="d-flex align-items-center gap-1"><MapPin size={11} />{request.location_name}</span>}
        {request.user_details && <span className="d-flex align-items-center gap-1"><Phone size={11} />{request.user_details.first_name} {request.user_details.last_name}{request.user_details.phone ? ` — ${request.user_details.phone}` : ''}</span>}
        {request.active_assignment?.distance_km && <span className="d-flex align-items-center gap-1"><MapPin size={11} />{Number(request.active_assignment.distance_km).toFixed(1)} km</span>}
      </div>
      <div className="d-flex gap-2">
        {request.status === 'ASSIGNED' && (
          <button className="btn btn-sm btn-outline-primary flex-grow-1 d-flex align-items-center justify-content-center gap-1" onClick={() => onAction(request.id, 'start')} disabled={loading}>
            <Play size={13} /> Start Work
          </button>
        )}
        {request.status === 'IN_PROGRESS' && (
          <button className="btn btn-sm btn-success flex-grow-1 d-flex align-items-center justify-content-center gap-1" onClick={() => onAction(request.id, 'complete')} disabled={loading}>
            <CheckCircle size={13} /> Complete Work
          </button>
        )}
      </div>
    </div>
  );
};

// ─── Dashboard Section ─────────────────────────────────────────────────────────
const Dashboard: React.FC = () => {
  const [assignments, setAssignments] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAssignments = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await apiRequests.list();
      setAssignments(data.filter((request) => request.status === 'ASSIGNED' || request.status === 'IN_PROGRESS'));
    } catch { setError('Failed to load assignments.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAssignments(); }, [fetchAssignments]);

  const handleAction = async (id: string, action: 'start' | 'complete') => {
    setActionLoading(true);
    try {
      if (action === 'start') await apiRequests.startWork(id);
      else await apiRequests.completeWork(id);
      await fetchAssignments();
    } catch { /* ignore */ }
    finally { setActionLoading(false); }
  };

  const urgent = assignments.filter(a => a.priority === 'URGENT' || a.priority === 'CRITICAL');
  const normal = assignments.filter(a => a.priority !== 'URGENT' && a.priority !== 'CRITICAL');

  return (
    <div>
      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3"><KPICard label="Active Assignments" value={assignments.length} color="var(--color-primary)" /></div>
        <div className="col-6 col-md-3"><KPICard label="Urgent" value={urgent.length} color="var(--color-danger)" /></div>
        <div className="col-6 col-md-3"><KPICard label="In Progress" value={assignments.filter(a => a.status === 'IN_PROGRESS').length} color="var(--color-warning)" /></div>
        <div className="col-6 col-md-3"><KPICard label="Assigned (Pending)" value={assignments.filter(a => a.status === 'ASSIGNED').length} color="var(--color-info)" /></div>
      </div>
      {error && <div className="alert alert-danger small py-2">{error}</div>}
      {loading ? (
        <>{Array.from({length:3}).map((_,i) => <SkeletonCard key={i} />)}</>
      ) : assignments.length === 0 ? (
        <EmptyState icon={<ClipboardList size={48} className="text-muted" />} title="No active assignments" description="You're all caught up! New assignments will appear here." />
      ) : (
        <>
          {urgent.length > 0 && (
            <div className="mb-3">
              <div className="d-flex align-items-center gap-2 mb-2"><AlertTriangle size={14} className="text-danger" /><span className="fw-semibold small text-danger">Urgent ({urgent.length})</span></div>
              {urgent.map(r => <EmpAssignmentCard key={r.id} request={r} onAction={handleAction} loading={actionLoading} />)}
            </div>
          )}
          {normal.length > 0 && (
            <div>
              {urgent.length > 0 && <div className="text-muted small fw-semibold mb-2">Normal Priority ({normal.length})</div>}
              {normal.map(r => <EmpAssignmentCard key={r.id} request={r} onAction={handleAction} loading={actionLoading} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ─── History Section ───────────────────────────────────────────────────────────
const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiRequests.list({ status: 'COMPLETED' }).then(d => { setHistory(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);
  if (loading) return <SkeletonTable rows={6} />;
  if (history.length === 0) return <EmptyState icon={<History size={48} className="text-muted" />} title="No completed assignments" description="Your work history will appear here after completing assignments." />;
  return (
    <div>
      <div className="fw-semibold mb-3 small text-muted">{history.length} completed assignments</div>
      <div className="table-responsive">
        <table className="table table-hover table-sm align-middle">
          <thead className="table-light small text-muted">
            <tr><th>Issue</th><th>Domain</th><th>Priority</th><th>Completed</th><th>Rating</th></tr>
          </thead>
          <tbody>
            {history.map(r => {
              const pc = getPriorityColors(r.priority);
              const title = r.predefined_issue_details?.title || r.custom_description?.substring(0, 40) || 'Service Request';
              const rating = r.feedback_details?.rating;
              return (
                <tr key={r.id}>
                  <td className="small fw-medium">{title}</td>
                  <td className="small text-muted">{r.domain_details?.name}</td>
                  <td><span className="badge rounded-pill" style={{ backgroundColor: pc.bg, color: pc.text, fontSize: '0.68rem' }}>{r.priority}</span></td>
                  <td className="small text-muted">{r.completed_at ? new Date(r.completed_at).toLocaleDateString() : '-'}</td>
                  <td>{rating ? <span className="d-flex align-items-center gap-1 small"><Star size={12} fill="#f59e0b" stroke="#f59e0b" />{rating}/5</span> : <span className="text-muted small">-</span>}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Profile Section ───────────────────────────────────────────────────────────
const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiEmployees.getMe().then(d => { setProfile(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);
  if (loading) return <SkeletonTable rows={4} />;
  if (!profile) return <EmptyState icon={<User size={48} className="text-muted" />} title="Profile not found" description="Your employee profile could not be loaded." />;
  const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return (
    <div className="row g-3">
      <div className="col-md-4">
        <div className="kpi-card text-center">
          <div className="rounded-circle d-flex align-items-center justify-content-center text-white fw-bold mx-auto mb-3" style={{ width: 64, height: 64, backgroundColor: 'var(--color-primary)', fontSize: '1.5rem' }}>
            {profile.user_details?.first_name?.[0] || 'E'}
          </div>
          <div className="fw-bold">{profile.user_details?.first_name} {profile.user_details?.last_name}</div>
          <div className="text-muted small">{profile.role_details?.title || 'Technician'}</div>
          <span className={`badge mt-2 ${profile.is_available ? 'bg-success' : 'bg-secondary'}`}>{profile.is_available ? 'Available' : 'Unavailable'}</span>
        </div>
      </div>
      <div className="col-md-8">
        <div className="kpi-card mb-3">
          <div className="text-muted small fw-medium mb-3">Performance Stats</div>
          <div className="row g-2 text-center">
            <div className="col-3"><div className="fw-bold" style={{ color: 'var(--color-primary)' }}>{profile.historical_completed_count || 0}</div><div className="text-muted" style={{ fontSize: '0.7rem' }}>Completed</div></div>
            <div className="col-3"><div className="fw-bold" style={{ color: 'var(--color-warning)' }}>{profile.active_assignments_count || 0}</div><div className="text-muted" style={{ fontSize: '0.7rem' }}>Active</div></div>
            <div className="col-3"><div className="fw-bold" style={{ color: 'var(--color-success)' }}>{profile.historical_avg_rating?.toFixed(1) || '—'}</div><div className="text-muted" style={{ fontSize: '0.7rem' }}>Avg Rating</div></div>
            <div className="col-3"><div className="fw-bold" style={{ color: 'var(--color-info)' }}>{profile.experience_years}y</div><div className="text-muted" style={{ fontSize: '0.7rem' }}>Experience</div></div>
          </div>
        </div>
        {profile.skills && profile.skills.length > 0 && (
          <div className="kpi-card mb-3">
            <div className="text-muted small fw-medium mb-2">Skills</div>
            <div className="d-flex flex-wrap gap-2">
              {profile.skills.map(s => (
                <span key={s.id} className="badge rounded-pill fw-medium" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)', fontSize: '0.72rem' }}>
                  {s.domain_name} <span className="text-muted">Lv{s.proficiency_level}</span>
                </span>
              ))}
            </div>
          </div>
        )}
        {profile.schedules && profile.schedules.length > 0 && (
          <div className="kpi-card">
            <div className="text-muted small fw-medium mb-2">Schedule</div>
            <div className="d-flex flex-wrap gap-2">
              {profile.schedules.filter(s => s.is_active).map(s => (
                <span key={s.id} className="badge rounded-pill" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-primary)', border: '1px solid var(--color-border)', fontSize: '0.7rem' }}>
                  {DAY_NAMES[s.day_of_week]} {s.start_time?.substring(0,5)}–{s.end_time?.substring(0,5)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Main EmployeePortal ───────────────────────────────────────────────────────
export const EmployeePortal: React.FC = () => {
  const [activeSection, setActiveSection] = useState<Section>('dashboard');
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={16} /> },
    { id: 'tasks',     label: 'My Tasks',  icon: <ClipboardList size={16} /> },
    { id: 'history',   label: 'History',   icon: <History size={16} /> },
    { id: 'profile',   label: 'Profile',   icon: <User size={16} /> },
  ];
  return (
    <div className="portal-layout">
      <Sidebar sections={navItems} activeSection={activeSection} onSelect={id => setActiveSection(id as Section)} />
      <div className="portal-content">
        <h5 className="fw-bold mb-1">{navItems.find(n => n.id === activeSection)?.label}</h5>
        <p className="text-muted small mb-4">
          {activeSection === 'dashboard' ? 'Your active assignments and workload'
            : activeSection === 'tasks'   ? 'Manage your current work'
            : activeSection === 'history' ? 'Past completed assignments'
            : 'Your skills, schedule, and performance'}
        </p>
        {activeSection === 'dashboard' && <Dashboard />}
        {activeSection === 'tasks'     && <Dashboard />}
        {activeSection === 'history'   && <HistoryPage />}
        {activeSection === 'profile'   && <ProfilePage />}
      </div>
    </div>
  );
};
