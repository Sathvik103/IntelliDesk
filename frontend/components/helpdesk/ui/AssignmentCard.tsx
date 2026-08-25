'use client';
import React from 'react';
import { ServiceRequest } from '@/lib/types';
import { getPriorityColors } from '@/lib/colors';
import { MapPin, Phone, AlertTriangle } from 'lucide-react';

interface AssignmentCardProps {
  request: ServiceRequest;
  onStartWork?: () => void;
  onCompleteWork?: () => void;
  isLoading?: boolean;
}

export const AssignmentCard: React.FC<AssignmentCardProps> = ({
  request,
  onStartWork,
  onCompleteWork,
  isLoading,
}) => {
  const pc = getPriorityColors(request.priority);
  const isUrgent = request.priority === 'URGENT' || request.priority === 'CRITICAL';
  const title =
    request.predefined_issue_details?.title ||
    request.custom_description?.substring(0, 60) ||
    'Service Request';

  return (
    <div
      className={`request-card mb-3 ${isUrgent ? 'border-danger' : ''}`}
      style={isUrgent ? { borderColor: 'var(--color-danger)', borderWidth: '2px' } : {}}
    >
      <div className="d-flex align-items-center gap-2 mb-2">
        {isUrgent && <AlertTriangle size={16} className="text-danger" />}
        <span
          className="badge rounded-pill fw-medium"
          style={{ backgroundColor: pc.bg, color: pc.text, fontSize: '0.72rem' }}
        >
          {request.priority_display || request.priority}
        </span>
        <span className="text-muted small ms-auto">{request.domain_details?.name}</span>
      </div>
      <div className="fw-semibold text-dark mb-2" style={{ fontSize: '0.9rem' }}>
        {title}
      </div>
      {request.location_name && (
        <div className="d-flex align-items-center gap-1 text-muted small mb-1">
          <MapPin size={12} />
          <span>{request.location_name}</span>
        </div>
      )}
      {request.user_details && (
        <div className="d-flex align-items-center gap-1 text-muted small mb-2">
          <Phone size={12} />
          <span>
            {request.user_details.first_name} {request.user_details.last_name}
            {request.user_details.phone ? ` — ${request.user_details.phone}` : ''}
          </span>
        </div>
      )}
      <div className="d-flex gap-2 mt-2">
        {request.status === 'ASSIGNED' && onStartWork && (
          <button
            className="btn btn-sm btn-outline-primary flex-grow-1"
            onClick={onStartWork}
            disabled={isLoading}
          >
            Start Work
          </button>
        )}
        {request.status === 'IN_PROGRESS' && onCompleteWork && (
          <button
            className="btn btn-sm btn-success flex-grow-1"
            onClick={onCompleteWork}
            disabled={isLoading}
          >
            Complete Work
          </button>
        )}
      </div>
    </div>
  );
};
