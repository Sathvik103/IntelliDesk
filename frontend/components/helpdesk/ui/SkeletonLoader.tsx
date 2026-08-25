'use client';
import React from 'react';

export const Skeleton: React.FC<{ className?: string; style?: React.CSSProperties }> = ({ className = '', style }) => (
  <span className={`placeholder ${className}`} style={style} />
);

export const SkeletonTable: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="placeholder-glow">
    <div className="d-flex gap-2 mb-3">
      {[3, 2, 1, 2].map((col, i) => (
        <span key={i} className={`placeholder col-${col}`} style={{ height: 14 }} />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="d-flex gap-2 mb-2">
        {[4, 2, 1, 2, 1].map((col, j) => (
          <span key={j} className={`placeholder col-${col}`} style={{ height: 12 }} />
        ))}
      </div>
    ))}
  </div>
);

export const SkeletonCard: React.FC = () => (
  <div className="kpi-card mb-3 placeholder-glow">
    <div className="d-flex gap-2 mb-2">
      <span className="placeholder rounded-pill col-2" style={{ height: 20 }} />
      <span className="placeholder rounded-pill col-2" style={{ height: 20 }} />
      <span className="placeholder rounded-pill col-2 ms-auto" style={{ height: 20 }} />
    </div>
    <span className="placeholder col-8 d-block mb-2" style={{ height: 14 }} />
    <div className="d-flex gap-3">
      <span className="placeholder col-3" style={{ height: 12 }} />
      <span className="placeholder col-3" style={{ height: 12 }} />
      <span className="placeholder col-2 ms-auto" style={{ height: 12 }} />
    </div>
  </div>
);
