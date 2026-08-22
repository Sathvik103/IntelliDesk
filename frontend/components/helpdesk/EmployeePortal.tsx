'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  Employee,
  ServiceRequest,
} from '@/lib/types';
import {
  apiEmployees,
  apiRequests,
} from '@/lib/api';
import {
  HardHat,
  MapPin,
  Clock,
  CheckCircle2,
  PlayCircle,
  Phone,
  AlertCircle,
  Star,
  RefreshCw,
  Award,
  Flame,
  Check,
} from 'lucide-react';

export const EmployeePortal: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Employee | null>(null);
  const [tasks, setTasks] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

  const loadEmployeeData = async () => {
    setLoading(true);
    try {
      const [empProfile, allReqs] = await Promise.all([
        apiEmployees.getMe().catch(() => null),
        apiRequests.list(),
      ]);
      setProfile(empProfile);
      setTasks(allReqs);
    } catch (err) {
      console.error('Failed to load employee profile/tasks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployeeData();
  }, [user]);

  const handleStartWork = async (requestId: string) => {
    setUpdatingTaskId(requestId);
    try {
      await apiRequests.startWork(requestId);
      loadEmployeeData();
    } catch (e) {
      console.error(e);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleCompleteWork = async (requestId: string) => {
    setUpdatingTaskId(requestId);
    try {
      await apiRequests.completeWork(requestId);
      loadEmployeeData();
    } catch (e) {
      console.error(e);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleToggleAvailability = async () => {
    if (!profile) return;
    try {
      await apiEmployees.toggleAvailability(profile.id, !profile.is_available);
      setProfile((prev) => (prev ? { ...prev, is_available: !prev.is_available } : null));
    } catch (e) {
      console.error(e);
    }
  };

  const activeTasks = tasks.filter(
    (t) => t.status === 'ASSIGNED' || t.status === 'IN_PROGRESS' || t.status === 'REOPENED'
  );
  const completedTasks = tasks.filter((t) => t.status === 'COMPLETED');

  return (
    <div className="container py-4 px-3 px-lg-4">
      {/* Header & Personal Scorecard */}
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
          <h4 className="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
            <span>Workforce Mobile Field Console</span>
            <span className="badge bg-warning text-dark border border-warning-subtle fs-6">
              Field Technician
            </span>
          </h4>
          <p className="text-muted small mb-0">
            Assigned tasks ordered by proximity, priority, and domain SLAs
          </p>
        </div>

        <div className="d-flex align-items-center gap-3">
          {profile && (
            <div className="d-flex align-items-center gap-2 bg-white px-3 py-2 rounded-3 shadow-sm border">
              <span className="small fw-semibold text-muted">Duty Availability:</span>
              <div className="form-check form-switch mb-0">
                <input
                  className="form-check-input"
                  type="checkbox"
                  role="switch"
                  checked={profile.is_available}
                  onChange={handleToggleAvailability}
                />
              </div>
              <span
                className={`badge ${
                  profile.is_available ? 'bg-success' : 'bg-secondary'
                }`}
              >
                {profile.is_available ? 'Online' : 'Off Duty'}
              </span>
            </div>
          )}

          <button
            onClick={loadEmployeeData}
            disabled={loading}
            className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1 rounded-3"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Sync Tasks</span>
          </button>
        </div>
      </div>

      {/* Technician Scorecard */}
      {profile && (
        <div className="row g-3 mb-4">
          <div className="col-6 col-md-3">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white">
              <small className="text-muted d-block">Active Workload</small>
              <div className="fs-4 fw-bold text-primary">
                {profile.active_assignments_count} / {profile.max_active_assignments}
              </div>
              <small className="text-muted">Concurrent active jobs</small>
            </div>
          </div>

          <div className="col-6 col-md-3">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white">
              <small className="text-muted d-block">Customer Satisfaction</small>
              <div className="fs-4 fw-bold text-warning">
                ⭐ {profile.historical_avg_rating.toFixed(1)} <small className="fs-6 text-muted">/ 5.0</small>
              </div>
              <small className="text-muted">From verified ratings</small>
            </div>
          </div>

          <div className="col-6 col-md-3">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white">
              <small className="text-muted d-block">Total Resolved</small>
              <div className="fs-4 fw-bold text-success">
                {profile.historical_completed_count} Jobs
              </div>
              <small className="text-muted">Lifetime completed</small>
            </div>
          </div>

          <div className="col-6 col-md-3">
            <div className="card border-0 shadow-sm rounded-3 p-3 bg-white">
              <small className="text-muted d-block">GPS Proximity Mode</small>
              <div className="fs-4 fw-bold text-danger">Active</div>
              <small className="text-muted">Haversine metric dispatch</small>
            </div>
          </div>
        </div>
      )}

      {/* Active Tasks Queue */}
      <div className="mb-5">
        <h5 className="fw-bold text-dark mb-3 d-flex align-items-center gap-2">
          <span>Active Assignment Queue</span>
          <span className="badge bg-primary rounded-pill">{activeTasks.length}</span>
        </h5>

        {activeTasks.length === 0 ? (
          <div className="card border-0 shadow-sm rounded-3 p-5 bg-white text-center">
            <CheckCircle2 size={48} className="text-success mx-auto mb-2" />
            <h6 className="fw-bold text-dark">Queue is All Clear!</h6>
            <p className="text-muted small mb-0">
              No pending service requests assigned to your queue at this moment.
            </p>
          </div>
        ) : (
          <div className="row g-3">
            {activeTasks.map((task) => {
              const assign = task.active_assignment;
              const isUpdating = updatingTaskId === task.id;
              return (
                <div key={task.id} className="col-12 col-lg-6">
                  <div
                    className={`card border-0 shadow-sm rounded-3 p-4 bg-white h-100 position-relative ${
                      task.status === 'IN_PROGRESS' ? 'border-start border-warning border-4' : ''
                    }`}
                  >
                    {/* Top badging */}
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <div className="d-flex align-items-center gap-2">
                        <span className="badge bg-dark">
                          {task.domain_details?.name || 'Trade Job'}
                        </span>
                        <span
                          className={`badge ${
                            task.priority === 'CRITICAL' || task.priority === 'URGENT'
                              ? 'bg-danger'
                              : task.priority === 'HIGH'
                              ? 'bg-warning text-dark'
                              : 'bg-info text-dark'
                          }`}
                        >
                          {task.priority_display || task.priority}
                        </span>
                      </div>

                      {assign && (
                        <div className="badge bg-danger-subtle text-danger border border-danger-subtle fs-6 py-1 px-2 d-flex align-items-center gap-1">
                          <MapPin size={14} />
                          <span>{assign.distance_km.toFixed(2)} km away</span>
                        </div>
                      )}
                    </div>

                    {/* Title & Description */}
                    <h6 className="fw-bold text-dark mb-1">
                      {task.predefined_issue_details?.title || 'Service Request'}
                    </h6>
                    <p className="text-secondary small mb-3">
                      {task.custom_description || 'No additional custom details provided.'}
                    </p>

                    {/* Customer & Location */}
                    <div className="p-3 bg-light rounded-3 mb-3 small">
                      <div className="d-flex justify-content-between mb-1">
                        <span className="text-muted">Location:</span>
                        <strong className="text-dark">{task.location_name || 'Resident Unit'}</strong>
                      </div>
                      <div className="d-flex justify-content-between mb-1">
                        <span className="text-muted">Resident:</span>
                        <span className="text-dark">
                          {task.user_details?.first_name
                            ? `${task.user_details.first_name} ${task.user_details.last_name}`
                            : task.user_details?.username}
                        </span>
                      </div>
                      {task.user_details?.phone && (
                        <div className="d-flex justify-content-between">
                          <span className="text-muted">Phone:</span>
                          <a
                            href={`tel:${task.user_details.phone}`}
                            className="text-primary text-decoration-none fw-semibold d-flex align-items-center gap-1"
                          >
                            <Phone size={12} />
                            {task.user_details.phone}
                          </a>
                        </div>
                      )}
                    </div>

                    {/* Action Workflow Buttons */}
                    <div className="mt-auto d-flex gap-2">
                      {task.status === 'ASSIGNED' || task.status === 'REOPENED' ? (
                        <button
                          onClick={() => handleStartWork(task.id)}
                          disabled={isUpdating}
                          className="btn btn-warning flex-fill fw-semibold d-flex align-items-center justify-content-center gap-2 rounded-3 text-dark"
                        >
                          <PlayCircle size={16} />
                          <span>{isUpdating ? 'Updating...' : 'Start Work (In-Progress)'}</span>
                        </button>
                      ) : task.status === 'IN_PROGRESS' ? (
                        <button
                          onClick={() => handleCompleteWork(task.id)}
                          disabled={isUpdating}
                          className="btn btn-success flex-fill fw-semibold d-flex align-items-center justify-content-center gap-2 rounded-3"
                        >
                          <CheckCircle2 size={16} />
                          <span>{isUpdating ? 'Saving...' : 'Mark Completed'}</span>
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Completed History */}
      <div>
        <h5 className="fw-bold text-dark mb-3">Recently Completed Jobs</h5>
        <div className="card border-0 shadow-sm rounded-3 bg-white p-4">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0 small">
              <thead className="table-light">
                <tr>
                  <th>Job Title</th>
                  <th>Location</th>
                  <th>Resolved At</th>
                  <th>Distance at Dispatch</th>
                  <th>Customer Rating & Review</th>
                </tr>
              </thead>
              <tbody>
                {completedTasks.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-4 text-muted">
                      No completed jobs recorded yet.
                    </td>
                  </tr>
                ) : (
                  completedTasks.slice(0, 10).map((req) => (
                    <tr key={req.id}>
                      <td className="fw-semibold text-dark">
                        {req.predefined_issue_details?.title || req.custom_description}
                      </td>
                      <td>{req.location_name}</td>
                      <td className="text-muted">
                        {req.completed_at ? new Date(req.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Completed'}
                      </td>
                      <td>
                        <span className="badge bg-light text-dark border">
                          {req.active_assignment?.distance_km ? `${req.active_assignment.distance_km.toFixed(2)} km` : '—'}
                        </span>
                      </td>
                      <td>
                        {req.feedback_details ? (
                          <div>
                            <span className="text-warning fw-semibold">
                              {'⭐'.repeat(req.feedback_details.rating)}
                            </span>
                            {req.feedback_details.comments && (
                              <div className="text-muted text-truncate" style={{ maxWidth: 260 }}>
                                &ldquo;{req.feedback_details.comments}&rdquo;
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-muted">Pending customer review</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
