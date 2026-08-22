'use client';

import React, { useEffect, useState } from 'react';
import { apiRequests } from '@/lib/api';
import { CandidateInspectorItem } from '@/lib/types';
import {
  Sparkles,
  MapPin,
  Star,
  CheckCircle2,
  Briefcase,
  AlertCircle,
  X,
  Gauge,
  Cpu,
} from 'lucide-react';

interface CandidateInspectorModalProps {
  requestId: string | null;
  onClose: () => void;
}

export const CandidateInspectorModal: React.FC<CandidateInspectorModalProps> = ({
  requestId,
  onClose,
}) => {
  const [candidates, setCandidates] = useState<CandidateInspectorItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [domainName, setDomainName] = useState<string>('');
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateInspectorItem | null>(null);

  useEffect(() => {
    if (!requestId) return;

    const fetchCandidates = async () => {
      setLoading(true);
      try {
        const data = await apiRequests.inspectCandidates(requestId);
        setCandidates(data.candidates || []);
        if (data.candidates && data.candidates.length > 0) {
          setSelectedCandidate(data.candidates[0]);
        }
      } catch (err) {
        console.error('Failed to inspect candidates', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
  }, [requestId]);

  if (!requestId) return null;

  return (
    <div
      className="modal show d-block"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.55)', zIndex: 1050 }}
      tabIndex={-1}
    >
      <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div className="modal-content shadow-lg border-0 rounded-4">
          {/* Header */}
          <div className="modal-header bg-dark text-white border-bottom border-secondary py-3 px-4 rounded-top-4">
            <div className="d-flex align-items-center gap-2">
              <div className="bg-primary text-white p-2 rounded-3">
                <Cpu size={20} />
              </div>
              <div>
                <h5 className="modal-title fw-bold mb-0">
                  Workforce Assignment & Ranking Engine Inspector
                </h5>
                <small className="text-muted">
                  Inspecting candidate eligibility, Haversine distance, and suitability scoring
                </small>
              </div>
            </div>
            <button
              type="button"
              className="btn-close btn-close-white"
              onClick={onClose}
              aria-label="Close"
            />
          </div>

          {/* Body */}
          <div className="modal-body p-4 bg-light">
            {/* Info Banner */}
            <div className="alert alert-info border-0 rounded-3 d-flex align-items-start gap-3 mb-4 shadow-sm">
              <Sparkles size={22} className="text-info flex-shrink-0 mt-1" />
              <div className="small">
                <strong>Two-Stage Assignment Pipeline:</strong>
                <p className="mb-0 text-secondary">
                  <strong>Stage 1 (Hard Rules):</strong> Filters out candidates from other organizations, missing trade skills, on-leave status, or exceeded workload capacity.
                  <br />
                  <strong>Stage 2 (Scoring & Ranking):</strong> Evaluates proximity via Haversine distance, skill proficiency, historical ratings, and capacity. The interface is modular and replaceable with external ML models.
                </p>
              </div>
            </div>

            {loading ? (
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading candidates...</span>
                </div>
                <p className="text-muted mt-2 small">Analyzing eligible workforce candidates...</p>
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-5 bg-white rounded-3 border">
                <AlertCircle size={40} className="text-warning mb-2" />
                <h6 className="fw-bold">No Eligible Candidates Found</h6>
                <p className="text-muted small mb-0">
                  All technicians for this domain are either off-duty, at maximum workload capacity, or unavailable.
                </p>
              </div>
            ) : (
              <div className="row g-4">
                {/* Left Candidate List */}
                <div className="col-lg-6">
                  <h6 className="fw-bold text-dark mb-3 d-flex align-items-center justify-content-between">
                    <span>Ranked Candidates ({candidates.length})</span>
                    <span className="badge bg-secondary">Sorted by Suitability</span>
                  </h6>

                  <div className="d-flex flex-column gap-3">
                    {candidates.map((cand, idx) => {
                      const isSelected = selectedCandidate?.employee_id === cand.employee_id;
                      return (
                        <div
                          key={cand.employee_id}
                          onClick={() => setSelectedCandidate(cand)}
                          className={`card border-0 shadow-sm rounded-3 p-3 cursor-pointer transition-all ${
                            isSelected ? 'border-start border-primary border-4 bg-white ring-1' : 'bg-white'
                          }`}
                          style={{
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                          }}
                        >
                          <div className="d-flex justify-content-between align-items-start mb-2">
                            <div className="d-flex align-items-center gap-2">
                              <span
                                className={`badge rounded-circle p-2 ${
                                  idx === 0 ? 'bg-success text-white' : 'bg-light text-dark'
                                }`}
                                style={{ width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                              >
                                #{idx + 1}
                              </span>
                              <div>
                                <h6 className="mb-0 fw-bold text-dark">{cand.employee_name}</h6>
                                <small className="text-muted">{cand.role_title}</small>
                              </div>
                            </div>

                            <div className="text-end">
                              <div className="fw-bold text-primary fs-5">
                                {(cand.suitability_score * 100).toFixed(1)}%
                              </div>
                              <small className="text-muted" style={{ fontSize: '0.7rem' }}>
                                Suitability Score
                              </small>
                            </div>
                          </div>

                          <div className="row g-2 text-muted small mt-1">
                            <div className="col-4 d-flex align-items-center gap-1">
                              <MapPin size={14} className="text-danger" />
                              <span>{cand.distance_km.toFixed(2)} km</span>
                            </div>
                            <div className="col-4 d-flex align-items-center gap-1">
                              <Star size={14} className="text-warning fill-warning" />
                              <span>{cand.historical_avg_rating.toFixed(1)} / 5</span>
                            </div>
                            <div className="col-4 d-flex align-items-center gap-1">
                              <Briefcase size={14} className="text-primary" />
                              <span>{cand.current_active_jobs} Active</span>
                            </div>
                          </div>

                          {idx === 0 && (
                            <div className="mt-2 pt-2 border-top d-flex align-items-center justify-content-between">
                              <span className="badge bg-success-subtle text-success border border-success-subtle">
                                <CheckCircle2 size={12} className="me-1" />
                                Top Recommended Match
                              </span>
                              <small className="text-muted" style={{ fontSize: '0.72rem' }}>
                                Highest composite score
                              </small>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Right Feature Breakdown Inspector */}
                <div className="col-lg-6">
                  {selectedCandidate ? (
                    <div className="card border-0 shadow-sm rounded-3 p-4 bg-white h-100">
                      <div className="d-flex align-items-center justify-content-between mb-3 border-bottom pb-3">
                        <div>
                          <h6 className="fw-bold text-dark mb-0">{selectedCandidate.employee_name}</h6>
                          <small className="text-muted">Feature Vector & Scoring Breakdown</small>
                        </div>
                        <span className="badge bg-primary fs-6">
                          Score: {selectedCandidate.suitability_score.toFixed(3)}
                        </span>
                      </div>

                      {/* Metrics grid */}
                      <div className="row g-3 mb-4">
                        <div className="col-6">
                          <div className="p-3 bg-light rounded-3">
                            <small className="text-muted d-block">Haversine Distance</small>
                            <span className="fs-5 fw-bold text-danger">
                              {selectedCandidate.distance_km.toFixed(2)} km
                            </span>
                            <small className="d-block text-muted" style={{ fontSize: '0.7rem' }}>
                              Calculated from lat/lng
                            </small>
                          </div>
                        </div>

                        <div className="col-6">
                          <div className="p-3 bg-light rounded-3">
                            <small className="text-muted d-block">Domain Skill Level</small>
                            <span className="fs-5 fw-bold text-primary">
                              Level {selectedCandidate.domain_proficiency} / 5
                            </span>
                            <small className="d-block text-muted" style={{ fontSize: '0.7rem' }}>
                              Trade certified
                            </small>
                          </div>
                        </div>

                        <div className="col-6">
                          <div className="p-3 bg-light rounded-3">
                            <small className="text-muted d-block">Current Workload</small>
                            <span className="fs-5 fw-bold text-dark">
                              {selectedCandidate.current_active_jobs} Jobs
                            </span>
                            <small className="d-block text-muted" style={{ fontSize: '0.7rem' }}>
                              Under max capacity limit
                            </small>
                          </div>
                        </div>

                        <div className="col-6">
                          <div className="p-3 bg-light rounded-3">
                            <small className="text-muted d-block">Historical Rating</small>
                            <span className="fs-5 fw-bold text-warning">
                              ⭐ {selectedCandidate.historical_avg_rating.toFixed(1)} / 5.0
                            </span>
                            <small className="d-block text-muted" style={{ fontSize: '0.7rem' }}>
                              Customer satisfaction
                            </small>
                          </div>
                        </div>
                      </div>

                      {/* Raw Feature Vector JSON */}
                      <div className="mt-auto">
                        <label className="form-label fw-semibold text-muted small mb-1">
                          Extracted ML Feature Vector (Stored in Assignment Snapshot):
                        </label>
                        <pre
                          className="bg-dark text-success p-3 rounded-3 small overflow-auto mb-0"
                          style={{ maxHeight: 200, fontSize: '0.75rem' }}
                        >
                          {JSON.stringify(selectedCandidate.features, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="modal-footer bg-white border-top px-4 py-3 rounded-bottom-4">
            <button type="button" className="btn btn-secondary px-4" onClick={onClose}>
              Close Inspector
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
