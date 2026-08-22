'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  ServiceRequest,
  ServiceDomain,
  PredefinedIssue,
  PriorityType,
} from '@/lib/types';
import {
  apiRequests,
  apiServices,
} from '@/lib/api';
import {
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Phone,
  Star,
  RefreshCw,
  Zap,
  Droplets,
  Fan,
  Hammer,
  Shield,
  Wifi,
  Wrench,
  Sparkles,
  ArrowRight,
  MessageSquare,
} from 'lucide-react';

interface ResidentPortalProps {
  onOpenFeedback: (request: ServiceRequest) => void;
}

const DOMAIN_ICONS: Record<string, React.ReactNode> = {
  Electrical: <Zap size={20} className="text-warning" />,
  Plumbing: <Droplets size={20} className="text-info" />,
  'HVAC & Air Conditioning': <Fan size={20} className="text-primary" />,
  'Carpentry & Civil': <Hammer size={20} className="text-secondary" />,
  'Security & Surveillance': <Shield size={20} className="text-danger" />,
  'IT & Network Infrastructure': <Wifi size={20} className="text-success" />,
  'General Maintenance': <Wrench size={20} className="text-dark" />,
};

export const ResidentPortal: React.FC<ResidentPortalProps> = ({ onOpenFeedback }) => {
  const { user, organization } = useAuth();
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [domains, setDomains] = useState<ServiceDomain[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // New Request Modal / State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [selectedDomainId, setSelectedDomainId] = useState<string>('');
  const [selectedIssueId, setSelectedIssueId] = useState<string>('custom');
  const [customDescription, setCustomDescription] = useState<string>('');
  const [locationName, setLocationName] = useState<string>(user?.address || 'Tower A, Apt 402');
  const [priority, setPriority] = useState<PriorityType>('NORMAL');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitSuccessMsg, setSubmitSuccessMsg] = useState<string | null>(null);

  const loadResidentData = React.useCallback(async () => {
    setLoading(true);
    try {
      const [reqRes, domRes] = await Promise.all([
        apiRequests.list(),
        apiServices.listDomains(),
      ]);
      setRequests(reqRes);
      setDomains(domRes);
      if (domRes.length > 0 && !selectedDomainId) {
        setSelectedDomainId(domRes[0].id);
      }
    } catch (err) {
      console.error('Failed to load resident data', err);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    loadResidentData();
  }, [loadResidentData]);

  const activeDomain = domains.find((d) => d.id === selectedDomainId);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDomainId) return;

    setSubmitting(true);
    setSubmitSuccessMsg(null);

    const isCustom = selectedIssueId === 'custom';
    const payload = {
      domain: selectedDomainId,
      predefined_issue: isCustom ? null : selectedIssueId,
      custom_description: customDescription,
      location_name: locationName,
      priority,
      latitude: organization?.latitude || 12.9304,
      longitude: organization?.longitude || 77.6784,
    };

    try {
      const newReq = await apiRequests.create(payload);
      setSubmitSuccessMsg('Request submitted successfully! Automated workforce assignment completed.');
      setTimeout(() => {
        setShowCreateModal(false);
        setCustomDescription('');
        setSelectedIssueId('custom');
        setSubmitSuccessMsg(null);
        loadResidentData();
      }, 1200);
    } catch (err: any) {
      console.error('Failed to create request', err);
    } finally {
      setSubmitting(false);
    }
  };

  const activeRequests = requests.filter((r) => r.status !== 'COMPLETED' && r.status !== 'CANCELLED');
  const completedRequests = requests.filter((r) => r.status === 'COMPLETED');

  return (
    <div className="container py-4 px-3 px-lg-4">
      {/* Top Banner */}
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
          <h4 className="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
            <span>Resident Service Center</span>
            <span className="badge bg-success-subtle text-success border border-success-subtle fs-6">
              {organization?.name || 'Community Portal'}
            </span>
          </h4>
          <p className="text-muted small mb-0">
            Submit service requests with automated technician assignment and real-time status tracking
          </p>
        </div>

        <div className="d-flex align-items-center gap-2">
          <button
            onClick={loadResidentData}
            disabled={loading}
            className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1 rounded-3"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary d-flex align-items-center gap-2 px-3 py-2 rounded-3 shadow-sm fw-semibold"
          >
            <PlusCircle size={18} />
            <span>Raise New Request</span>
          </button>
        </div>
      </div>

      {/* Active Requests Section */}
      <div className="mb-5">
        <h5 className="fw-bold text-dark mb-3 d-flex align-items-center gap-2">
          <span>Active Requests</span>
          <span className="badge bg-primary rounded-pill">{activeRequests.length}</span>
        </h5>

        {activeRequests.length === 0 ? (
          <div className="card border-0 shadow-sm rounded-3 p-5 bg-white text-center">
            <div className="bg-light p-3 rounded-circle d-inline-flex mb-3 mx-auto">
              <CheckCircle2 size={40} className="text-success" />
            </div>
            <h6 className="fw-bold text-dark">No Pending Requests</h6>
            <p className="text-muted small mb-3">
              Need electrical, plumbing, HVAC, or general maintenance repair?
            </p>
            <div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-outline-primary btn-sm px-3 rounded-3"
              >
                Raise a Request Now
              </button>
            </div>
          </div>
        ) : (
          <div className="row g-4">
            {activeRequests.map((req) => {
              const assign = req.active_assignment;
              const isAssigned = Boolean(assign);
              const isInProgress = req.status === 'IN_PROGRESS';

              return (
                <div key={req.id} className="col-12 col-lg-6">
                  <div className="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                    {/* Header */}
                    <div className="d-flex justify-content-between align-items-start mb-3">
                      <div className="d-flex align-items-center gap-2">
                        <div className="p-2 bg-light rounded-3">
                          {DOMAIN_ICONS[req.domain_details?.name || ''] || <Wrench size={20} />}
                        </div>
                        <div>
                          <h6 className="fw-bold text-dark mb-0">
                            {req.domain_details?.name || 'Service Request'}
                          </h6>
                          <small className="text-muted">ID: #{req.id.slice(0, 8)}</small>
                        </div>
                      </div>

                      <span
                        className={`badge ${
                          req.priority === 'CRITICAL' || req.priority === 'URGENT'
                            ? 'bg-danger'
                            : req.priority === 'HIGH'
                            ? 'bg-warning text-dark'
                            : 'bg-primary'
                        }`}
                      >
                        {req.priority_display || req.priority}
                      </span>
                    </div>

                    {/* Problem Description */}
                    <h6 className="fw-bold text-dark mb-1">
                      {req.predefined_issue_details?.title || 'Custom Service Request'}
                    </h6>
                    <p className="text-secondary small mb-3">
                      {req.custom_description || 'No additional custom description provided.'}
                    </p>

                    {/* Visual Progress Timeline */}
                    <div className="p-3 bg-light rounded-3 mb-3">
                      <small className="fw-semibold text-muted d-block mb-2">
                        Live Progress Status:
                      </small>
                      <div className="d-flex align-items-center justify-content-between position-relative">
                        <div className="text-center flex-fill">
                          <div className="badge bg-success rounded-circle p-2 mb-1">✓</div>
                          <div className="small fw-semibold text-dark" style={{ fontSize: '0.72rem' }}>
                            Created
                          </div>
                        </div>

                        <div className="text-center flex-fill">
                          <div
                            className={`badge rounded-circle p-2 mb-1 ${
                              isAssigned ? 'bg-success' : 'bg-warning text-dark'
                            }`}
                          >
                            {isAssigned ? '✓' : '...'}
                          </div>
                          <div className="small fw-semibold text-dark" style={{ fontSize: '0.72rem' }}>
                            Assigned
                          </div>
                        </div>

                        <div className="text-center flex-fill">
                          <div
                            className={`badge rounded-circle p-2 mb-1 ${
                              isInProgress ? 'bg-primary animate-pulse' : 'bg-secondary'
                            }`}
                          >
                            {isInProgress ? '⚡' : '3'}
                          </div>
                          <div className="small fw-semibold text-dark" style={{ fontSize: '0.72rem' }}>
                            In Progress
                          </div>
                        </div>

                        <div className="text-center flex-fill">
                          <div className="badge bg-secondary rounded-circle p-2 mb-1">4</div>
                          <div className="small text-muted" style={{ fontSize: '0.72rem' }}>
                            Resolved
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Assigned Technician Card */}
                    {assign ? (
                      <div className="p-3 border rounded-3 bg-white mb-3 d-flex justify-content-between align-items-center">
                        <div>
                          <div className="small text-muted">Assigned Specialist:</div>
                          <strong className="text-dark fs-6">{assign.employee_name}</strong>
                          <div className="text-danger small fw-semibold">
                            📍 {assign.distance_km.toFixed(2)} km from location
                          </div>
                        </div>

                        {assign.employee_phone && (
                          <a
                            href={`tel:${assign.employee_phone}`}
                            className="btn btn-outline-primary btn-sm d-flex align-items-center gap-1 rounded-3"
                          >
                            <Phone size={13} />
                            <span>Call</span>
                          </a>
                        )}
                      </div>
                    ) : (
                      <div className="alert alert-warning py-2 small mb-3">
                        Finding nearest certified technician...
                      </div>
                    )}

                    <div className="mt-auto d-flex justify-content-between align-items-center text-muted small pt-2 border-top">
                      <span>Location: <strong className="text-dark">{req.location_name}</strong></span>
                      <span>Target SLA: {req.domain_details?.sla_hours || 12} hrs</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Completed History & Ratings */}
      <div>
        <h5 className="fw-bold text-dark mb-3">Service History & Ratings</h5>
        <div className="card border-0 shadow-sm rounded-3 bg-white p-4">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0 small">
              <thead className="table-light">
                <tr>
                  <th>Domain & Issue</th>
                  <th>Resolved By</th>
                  <th>Location</th>
                  <th>Completion Time</th>
                  <th>Feedback & Rating</th>
                  <th className="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                {completedRequests.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-4 text-muted">
                      No resolved requests recorded yet.
                    </td>
                  </tr>
                ) : (
                  completedRequests.map((req) => {
                    const fb = req.feedback_details;
                    return (
                      <tr key={req.id}>
                        <td>
                          <div className="fw-bold text-dark">{req.domain_details?.name}</div>
                          <div className="text-muted">
                            {req.predefined_issue_details?.title || req.custom_description}
                          </div>
                        </td>
                        <td>{req.active_assignment?.employee_name || 'Staff'}</td>
                        <td>{req.location_name}</td>
                        <td className="text-muted">
                          {req.completed_at ? new Date(req.completed_at).toLocaleDateString() : 'Completed'}
                        </td>
                        <td>
                          {fb ? (
                            <div>
                              <span className="text-warning fw-semibold">
                                {'⭐'.repeat(fb.rating)}
                              </span>
                              {fb.comments && (
                                <div className="text-muted text-truncate" style={{ maxWidth: 200 }}>
                                  &ldquo;{fb.comments}&rdquo;
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="badge bg-warning text-dark">
                              Feedback Pending
                            </span>
                          )}
                        </td>
                        <td className="text-end">
                          {!fb ? (
                            <button
                              onClick={() => onOpenFeedback(req)}
                              className="btn btn-primary btn-sm rounded-3 fw-semibold"
                            >
                              Rate Service
                            </button>
                          ) : (
                            <span className="text-success small fw-semibold">
                              ✓ Reviewed
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Raise Request Modal */}
      {showCreateModal && (
        <div
          className="modal show d-block"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}
          tabIndex={-1}
        >
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content border-0 shadow-lg rounded-4">
              <div className="modal-header bg-primary text-white border-0 py-3 px-4 rounded-top-4">
                <div className="d-flex align-items-center gap-2">
                  <Sparkles size={20} />
                  <h5 className="modal-title fw-bold mb-0">Raise New Service Request</h5>
                </div>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setShowCreateModal(false)}
                />
              </div>

              <form onSubmit={handleCreateRequest}>
                <div className="modal-body p-4">
                  {submitSuccessMsg && (
                    <div className="alert alert-success d-flex align-items-center gap-2 small">
                      <CheckCircle2 size={16} />
                      <span>{submitSuccessMsg}</span>
                    </div>
                  )}

                  {/* Step 1: Select Domain */}
                  <div className="mb-4">
                    <label className="form-label fw-bold text-dark mb-2">
                      1. Select Service Trade / Domain:
                    </label>
                    <div className="row g-2">
                      {domains.map((dom) => {
                        const isSelected = dom.id === selectedDomainId;
                        return (
                          <div key={dom.id} className="col-6 col-md-3">
                            <div
                              onClick={() => {
                                setSelectedDomainId(dom.id);
                                setSelectedIssueId('custom');
                              }}
                              className={`p-3 rounded-3 border text-center cursor-pointer transition-all ${
                                isSelected
                                  ? 'border-primary bg-primary-subtle text-primary fw-bold shadow-sm'
                                  : 'bg-light text-dark'
                              }`}
                              style={{ cursor: 'pointer' }}
                            >
                              <div className="mb-1">{DOMAIN_ICONS[dom.name] || <Wrench size={22} />}</div>
                              <div className="small text-truncate">{dom.name}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Step 2: Common Issue or Custom Description */}
                  {activeDomain && (
                    <div className="mb-4">
                      <label className="form-label fw-bold text-dark mb-2">
                        2. Describe the Problem:
                      </label>

                      {activeDomain.predefined_issues && activeDomain.predefined_issues.length > 0 && (
                        <div className="mb-3">
                          <label className="form-label text-muted small">Choose Common Predefined Issue:</label>
                          <select
                            className="form-select mb-2"
                            value={selectedIssueId}
                            onChange={(e) => {
                              setSelectedIssueId(e.target.value);
                              if (e.target.value !== 'custom') {
                                const issue = activeDomain.predefined_issues?.find((i) => i.id === e.target.value);
                                if (issue) {
                                  setPriority(issue.default_priority);
                                }
                              }
                            }}
                          >
                            <option value="custom">-- Custom Description / Other Problem --</option>
                            {activeDomain.predefined_issues.map((iss) => (
                              <option key={iss.id} value={iss.id}>
                                {iss.title} (Priority: {iss.default_priority})
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      <textarea
                        className="form-control"
                        rows={3}
                        placeholder="Provide details about what is broken, room location, noises, or urgency..."
                        value={customDescription}
                        onChange={(e) => setCustomDescription(e.target.value)}
                        required={selectedIssueId === 'custom'}
                      />
                    </div>
                  )}

                  {/* Step 3: Location and Priority */}
                  <div className="row g-3">
                    <div className="col-12 col-md-6">
                      <label className="form-label fw-bold text-dark">
                        3. Location / Apartment Unit:
                      </label>
                      <div className="input-group">
                        <span className="input-group-text bg-light">
                          <MapPin size={15} className="text-danger" />
                        </span>
                        <input
                          type="text"
                          className="form-control"
                          placeholder="e.g. Tower B, Flat 704"
                          value={locationName}
                          onChange={(e) => setLocationName(e.target.value)}
                          required
                        />
                      </div>
                    </div>

                    <div className="col-12 col-md-6">
                      <label className="form-label fw-bold text-dark">
                        Urgency / Priority:
                      </label>
                      <select
                        className="form-select"
                        value={priority}
                        onChange={(e) => setPriority(e.target.value as PriorityType)}
                      >
                        <option value="LOW">Low (Convenience repair)</option>
                        <option value="NORMAL">Normal (Standard SLA)</option>
                        <option value="HIGH">High (Impacts daily routine)</option>
                        <option value="URGENT">Urgent (Safety or water/power outage)</option>
                        <option value="CRITICAL">Critical (Emergency / Hazard)</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="modal-footer border-0 bg-light px-4 py-3 rounded-bottom-4">
                  <button
                    type="button"
                    className="btn btn-outline-secondary px-3"
                    onClick={() => setShowCreateModal(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary px-4 fw-semibold d-flex align-items-center gap-2"
                    disabled={submitting}
                  >
                    <span>{submitting ? 'Matching Technician...' : 'Dispatch Request'}</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
