'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, Clock3, MapPin, Phone, Plus, RefreshCw, X } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { apiRequests } from '@/lib/api';
import { ServiceRequest } from '@/lib/types';
import { EmptyState, RequestCard, SkeletonCard } from './ui';
import { RequestWizard } from './wizard/RequestWizard';

interface ResidentPortalProps { onOpenFeedback: (request: ServiceRequest) => void; }

const requestTitle = (request: ServiceRequest) => request.predefined_issue_details?.title || 'Custom service request';
const details = (request: ServiceRequest) => request.details_snapshot || (() => { try { return JSON.parse(request.custom_description); } catch { return {}; } })();

export const ResidentPortal: React.FC<ResidentPortalProps> = ({ onOpenFeedback }) => {
  const { user, organization } = useAuth();
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [selected, setSelected] = useState<ServiceRequest | null>(null);
  const loadRequests = useCallback(async () => { setLoading(true); setError(null); try { setRequests(await apiRequests.list()); } catch { setError('We could not load your service requests.'); } finally { setLoading(false); } }, []);
  useEffect(() => { loadRequests(); }, [loadRequests]);

  return <div className="container py-4 px-3" style={{ maxWidth: 980 }}>
    <header className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4"><div><p className="text-primary small fw-semibold text-uppercase mb-1">{organization?.name || 'Service center'}</p><h3 className="fw-bold mb-1">Hello, {user?.first_name || 'there'}</h3><p className="text-muted mb-0">Track your requests or let us know what needs attention.</p></div><div className="d-flex gap-2"><button className="btn btn-outline-secondary" onClick={loadRequests} disabled={loading} aria-label="Refresh"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /></button><button className="btn btn-primary d-flex align-items-center gap-2" onClick={() => setShowWizard(true)}><Plus size={18} />New request</button></div></header>
    {error && <div className="alert alert-danger d-flex justify-content-between align-items-center"><span>{error}</span><button className="btn btn-sm btn-outline-danger" onClick={loadRequests}>Retry</button></div>}
    <section className="card border-0 shadow-sm rounded-4"><div className="card-body p-3 p-md-4"><div className="d-flex justify-content-between align-items-center mb-3"><h5 className="fw-bold mb-0">Your requests</h5><span className="badge text-bg-light">{requests.length}</span></div>
      {loading ? <>{[1, 2, 3].map((item) => <SkeletonCard key={item} />)}</> : requests.length === 0 ? <EmptyState icon={<CheckCircle2 size={48} />} title="No requests yet" description="Start a request whenever you need service support." action={{ label: 'Create your first request', onClick: () => setShowWizard(true) }} /> : <div className="row g-3">{requests.map((request) => <div className="col-12 col-md-6" key={request.id}><RequestCard request={request} onClick={() => setSelected(request)} /></div>)}</div>}
    </div></section>
    {showWizard && <RequestWizard onClose={() => setShowWizard(false)} onSuccess={() => { setShowWizard(false); loadRequests(); }} />}
    {selected && <div className="modal show d-block" style={{ backgroundColor: 'rgba(15,23,42,.6)', zIndex: 1055 }} role="dialog" aria-modal="true"><div className="modal-dialog modal-dialog-centered"><div className="modal-content border-0 shadow-lg rounded-4"><div className="modal-header border-0"><div><h5 className="fw-bold mb-1">{requestTitle(selected)}</h5><span className="text-muted small">#{selected.id.slice(0, 8)}</span></div><button className="btn btn-link text-muted" onClick={() => setSelected(null)}><X /></button></div><div className="modal-body pt-0"><div className="d-flex gap-2 text-muted small mb-3"><MapPin size={15} />{selected.location_name}</div><div className="border rounded-3 p-3 mb-3"><div className="fw-semibold small mb-2">Status timeline</div><div className="small d-flex flex-column gap-2"><span><CheckCircle2 size={14} className="text-success me-2" />Created {new Date(selected.created_at).toLocaleString()}</span>{selected.active_assignment && <span><CheckCircle2 size={14} className="text-success me-2" />Assigned to {selected.active_assignment.employee_name}</span>}{selected.in_progress_at && <span><Clock3 size={14} className="text-primary me-2" />Work started {new Date(selected.in_progress_at).toLocaleString()}</span>}{selected.completed_at && <span><CheckCircle2 size={14} className="text-success me-2" />Completed {new Date(selected.completed_at).toLocaleString()}</span>}</div></div>{selected.active_assignment && <div className="border rounded-3 p-3 mb-3"><div className="small text-muted">Your technician</div><div className="fw-semibold">{selected.active_assignment.employee_name}</div>{selected.active_assignment.employee_phone && <a className="small d-inline-flex align-items-center gap-1" href={`tel:${selected.active_assignment.employee_phone}`}><Phone size={13} />{selected.active_assignment.employee_phone}</a>}</div>}<div><div className="fw-semibold small mb-2">Request details</div><div className="d-flex flex-wrap gap-1">{Object.entries(details(selected)).map(([key, value]) => <span className="badge text-bg-light" key={key}>{key.replaceAll('_', ' ')}: {String(value)}</span>) || <span className="text-muted small">No structured details available.</span>}</div></div></div>{selected.status === 'COMPLETED' && !selected.feedback_details && <div className="modal-footer border-0"><button className="btn btn-primary btn-sm" onClick={() => onOpenFeedback(selected)}>Rate this service</button></div>}</div></div></div>}
  </div>;
};
