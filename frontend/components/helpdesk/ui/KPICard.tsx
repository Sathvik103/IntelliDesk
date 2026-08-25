'use client';
import React from 'react';

interface KPICardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
  trend?: number;
  subtitle?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  icon,
  color = 'var(--color-primary)',
  trend,
  subtitle,
}) => (
  <div className="kpi-card h-100">
    <div className="d-flex align-items-start justify-content-between mb-2">
      <div>
        <div className="text-muted small fw-medium mb-1">{label}</div>
        <div className="fw-bold" style={{ fontSize: '1.75rem', color, lineHeight: 1 }}>
          {value}
        </div>
        {subtitle && (
          <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
            {subtitle}
          </div>
        )}
      </div>
      {icon && (
        <div style={{ color, opacity: 0.7, fontSize: '1.5rem' }}>{icon}</div>
      )}
    </div>
    {trend != null && (
      <div className={`small fw-medium ${trend >= 0 ? 'text-success' : 'text-danger'}`}>
        {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs last period
      </div>
    )}
  </div>
);
