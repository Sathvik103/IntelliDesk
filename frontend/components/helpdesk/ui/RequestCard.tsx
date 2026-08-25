'use client';
import React from 'react';
import { ServiceRequest } from '@/lib/types';
import { getDomainColors, getPriorityColors, getStatusColors } from '@/lib/colors';
import { MapPin, User, Clock } from 'lucide-react';

interface RequestCardProps {
  request: ServiceRequest;
  onClick?: () => void;
}

export const RequestCard: React.FC<RequestCardProps> = ({ request, onClick }) => {
  const domainName = request.domain_details?.name || 'General';
  const dc = getDomainColors(domainName);
  const pc = getPriorityColors(request.priority);
  const sc = getStatusColors(request.status);
  const title =
    request.predefined_issue_details?.title ||
    (request.custom_description ? request.custom_description.substring(0, 60) : 'Service Request');

  return (
    <div
      className="request-card mb-3"
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="d-flex align-items-center gap-2 mb-2 flex-wrap">
        <span
          className="badge rounded-pill fw-medium"
          style={{ backgroundColor: dc.bg, color: dc.text, fontSize: '0.72rem' }}
        >
          {domainName}
        </span>
        <span
          className="badge rounded-pill fw-medium"
          style={{ backgroundColor: pc.bg, color: pc.text, fontSize: '0.72rem' }}
        >
          {request.priority_display || request.priority}
        </span>
        <span
          className="badge rounded-pill fw-medium ms-auto"
          style={{ backgroundColor: sc.bg, color: sc.text, fontSize: '0.72rem' }}
        >
          {request.status_display || request.status}
        </span>
      </div>
      <div className="fw-semibold text-dark mb-1" style={{ fontSize: '0.9rem' }}>
        {title}
      </div>
      {request.location_name && (
        <div className="d-flex align-items-center gap-1 text-muted small mb-1">
          <MapPin size={12} />
          <span>{request.location_name}</span>
        </div>
      )}
      {request.active_assignment && (
        <div className="d-flex align-items-center gap-1 text-muted small">
          <User size={12} />
          <span>{request.active_assignment.employee_name}</span>
        </div>
      )}
      <div className="d-flex align-items-center gap-1 text-muted mt-2" style={{ fontSize: '0.72rem' }}>
        <Clock size={11} />
        <span>{new Date(request.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  );
};
