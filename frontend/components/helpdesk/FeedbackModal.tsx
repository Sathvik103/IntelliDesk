'use client';

import React, { useState } from 'react';
import { apiFeedback } from '@/lib/api';
import { ServiceRequest } from '@/lib/types';
import { Star, CheckCircle, AlertTriangle, MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react';

interface FeedbackModalProps {
  request: ServiceRequest | null;
  onClose: () => void;
  onSubmitted: () => void;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  request,
  onClose,
  onSubmitted,
}) => {
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [isResolved, setIsResolved] = useState<boolean>(true);
  const [comments, setComments] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!request) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await apiFeedback.submit({
        request: request.id,
        is_resolved: isResolved,
        rating,
        comments,
      });
      onSubmitted();
      onClose();
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.error || 'Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const assignedTech = request.active_assignment?.employee_name || 'Staff Member';

  return (
    <div
      className="modal show d-block"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.55)', zIndex: 1050 }}
      tabIndex={-1}
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content border-0 shadow-lg rounded-4">
          {/* Header */}
          <div className="modal-header bg-primary text-white border-0 py-3 px-4 rounded-top-4">
            <h5 className="modal-title fw-bold">Service Feedback & Rating</h5>
            <button
              type="button"
              className="btn-close btn-close-white"
              onClick={onClose}
              aria-label="Close"
            />
          </div>

          <form onSubmit={handleSubmit}>
            <div className="modal-body p-4">
              {error && (
                <div className="alert alert-danger py-2 small mb-3">
                  {error}
                </div>
              )}

              {/* Request Summary Card */}
              <div className="bg-light p-3 rounded-3 mb-4 border">
                <small className="text-muted d-block mb-1">Service Request:</small>
                <div className="fw-semibold text-dark">
                  {request.predefined_issue_details?.title || request.custom_description}
                </div>
                <div className="small text-muted mt-1">
                  Serviced by: <strong className="text-dark">{assignedTech}</strong> ({request.domain_details?.name})
                </div>
              </div>

              {/* Resolution Confirmation Question */}
              <div className="mb-4">
                <label className="form-label fw-bold text-dark d-block">
                  Was your issue completely resolved?
                </label>
                <div className="d-flex gap-3 mt-2">
                  <button
                    type="button"
                    onClick={() => setIsResolved(true)}
                    className={`btn flex-fill py-2 d-flex align-items-center justify-content-center gap-2 rounded-3 ${
                      isResolved ? 'btn-success fw-bold' : 'btn-outline-secondary'
                    }`}
                  >
                    <ThumbsUp size={16} />
                    <span>Yes, Resolved</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setIsResolved(false)}
                    className={`btn flex-fill py-2 d-flex align-items-center justify-content-center gap-2 rounded-3 ${
                      !isResolved ? 'btn-danger fw-bold' : 'btn-outline-secondary'
                    }`}
                  >
                    <ThumbsDown size={16} />
                    <span>No, Unresolved</span>
                  </button>
                </div>
                {!isResolved && (
                  <div className="text-danger small mt-2 d-flex align-items-center gap-1">
                    <AlertTriangle size={14} />
                    <span>Marking as unresolved will automatically reopen the ticket and assign a senior technician.</span>
                  </div>
                )}
              </div>

              {/* Star Rating */}
              <div className="mb-4 text-center py-2 bg-light rounded-3 border">
                <label className="form-label fw-bold text-dark d-block mb-2">
                  Rate Technician&apos;s Quality of Work:
                </label>
                <div className="d-flex justify-content-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => {
                    const isFilled = (hoverRating !== null ? hoverRating : rating) >= star;
                    return (
                      <button
                        key={star}
                        type="button"
                        className="btn p-1 border-0 bg-transparent"
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(null)}
                        onClick={() => setRating(star)}
                      >
                        <Star
                          size={32}
                          className={`transition-all ${
                            isFilled ? 'text-warning fill-warning' : 'text-muted'
                          }`}
                          style={{ fill: isFilled ? '#ffc107' : 'none' }}
                        />
                      </button>
                    );
                  })}
                </div>
                <div className="small fw-semibold text-muted mt-1">
                  {rating === 5 && '⭐⭐⭐⭐⭐ Exceptional Service'}
                  {rating === 4 && '⭐⭐⭐⭐ Good / Satisfactory'}
                  {rating === 3 && '⭐⭐⭐ Average'}
                  {rating === 2 && '⭐⭐ Below Expectations'}
                  {rating === 1 && '⭐ Poor Service'}
                </div>
              </div>

              {/* Comments */}
              <div className="mb-3">
                <label className="form-label fw-bold text-dark d-flex align-items-center gap-1">
                  <MessageSquare size={15} />
                  <span>Comments or Feedback (Optional):</span>
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  placeholder="Share details about punctuality, problem resolution, or areas of improvement..."
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="modal-footer border-0 bg-light px-4 py-3 rounded-bottom-4">
              <button
                type="button"
                className="btn btn-outline-secondary px-3"
                onClick={onClose}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary px-4 fw-semibold"
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
