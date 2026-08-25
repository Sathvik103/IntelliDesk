export type DomainName =
  | 'Electrical'
  | 'Plumbing'
  | 'HVAC / AC'
  | 'Cleaning'
  | 'Carpentry'
  | 'Security'
  | 'IT Support'
  | 'General Maintenance';

export type PriorityLevel = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT' | 'CRITICAL';
export type StatusType =
  | 'CREATED'
  | 'QUEUED'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'REOPENED'
  | 'CANCELLED';

interface ColorConfig {
  bg: string;
  text: string;
  border: string;
  cssVar: string;
  badgeClass: string;
}

export const domainColorMap: Record<string, ColorConfig> = {
  'Electrical':          { bg: '#fef3c7', text: '#92400e', border: '#fcd34d', cssVar: 'var(--color-electrical)',  badgeClass: 'domain-badge-electrical' },
  'Plumbing':            { bg: '#dbeafe', text: '#1e40af', border: '#93c5fd', cssVar: 'var(--color-plumbing)',    badgeClass: 'domain-badge-plumbing'   },
  'HVAC / AC':           { bg: '#cffafe', text: '#164e63', border: '#67e8f9', cssVar: 'var(--color-hvac)',        badgeClass: 'domain-badge-hvac'       },
  'Cleaning':            { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7', cssVar: 'var(--color-cleaning)',    badgeClass: 'domain-badge-cleaning'   },
  'Carpentry':           { bg: '#fef3c7', text: '#78350f', border: '#fcd34d', cssVar: 'var(--color-carpentry)',   badgeClass: 'domain-badge-carpentry'  },
  'Security':            { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5', cssVar: 'var(--color-security)',    badgeClass: 'domain-badge-security'   },
  'IT Support':          { bg: '#e0e7ff', text: '#3730a3', border: '#a5b4fc', cssVar: 'var(--color-it-support)',  badgeClass: 'domain-badge-it-support' },
  'General Maintenance': { bg: '#f1f5f9', text: '#475569', border: '#cbd5e1', cssVar: 'var(--color-general)',     badgeClass: 'domain-badge-general'    },
};

export const priorityColorMap: Record<PriorityLevel, ColorConfig> = {
  LOW:      { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7', cssVar: 'var(--color-priority-low)',      badgeClass: 'priority-badge-low'      },
  NORMAL:   { bg: '#dbeafe', text: '#1e40af', border: '#93c5fd', cssVar: 'var(--color-priority-normal)',   badgeClass: 'priority-badge-normal'   },
  HIGH:     { bg: '#fef3c7', text: '#92400e', border: '#fcd34d', cssVar: 'var(--color-priority-high)',     badgeClass: 'priority-badge-high'     },
  URGENT:   { bg: '#ffedd5', text: '#9a3412', border: '#fdba74', cssVar: 'var(--color-priority-urgent)',   badgeClass: 'priority-badge-urgent'   },
  CRITICAL: { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5', cssVar: 'var(--color-priority-critical)', badgeClass: 'priority-badge-critical' },
};

export const statusColorMap: Record<StatusType, ColorConfig> = {
  CREATED:     { bg: '#f1f5f9', text: '#475569', border: '#cbd5e1', cssVar: '#64748b', badgeClass: 'status-badge-created'     },
  QUEUED:      { bg: '#e0e7ff', text: '#3730a3', border: '#a5b4fc', cssVar: '#6366f1', badgeClass: 'status-badge-assigned'    },
  ASSIGNED:    { bg: '#dbeafe', text: '#1e40af', border: '#93c5fd', cssVar: '#3b82f6', badgeClass: 'status-badge-assigned'    },
  IN_PROGRESS: { bg: '#fef3c7', text: '#92400e', border: '#fcd34d', cssVar: '#f59e0b', badgeClass: 'status-badge-in-progress' },
  COMPLETED:   { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7', cssVar: '#10b981', badgeClass: 'status-badge-completed'   },
  REOPENED:    { bg: '#ffedd5', text: '#9a3412', border: '#fdba74', cssVar: '#f97316', badgeClass: 'status-badge-reopened'    },
  CANCELLED:   { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5', cssVar: '#ef4444', badgeClass: 'status-badge-cancelled'   },
};

export function getDomainColors(domainName: string): ColorConfig {
  return domainColorMap[domainName] ?? domainColorMap['General Maintenance'];
}

export function getPriorityColors(priority: string): ColorConfig {
  return priorityColorMap[priority as PriorityLevel] ?? priorityColorMap['NORMAL'];
}

export function getStatusColors(status: string): ColorConfig {
  return statusColorMap[status as StatusType] ?? statusColorMap['CREATED'];
}
