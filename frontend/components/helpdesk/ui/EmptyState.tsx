'use client';
import React from 'react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => (
  <div className="text-center py-5">
    {icon && (
      <div className="text-muted mb-3" style={{ fontSize: '3rem' }}>
        {icon}
      </div>
    )}
    <h6 className="fw-semibold text-dark mb-1">{title}</h6>
    {description && <p className="text-muted small mb-3">{description}</p>}
    {action && (
      <button className="btn btn-primary btn-sm px-4" onClick={action.onClick}>
        {action.label}
      </button>
    )}
  </div>
);
