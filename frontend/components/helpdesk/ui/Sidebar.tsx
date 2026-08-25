'use client';
import React from 'react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
}

interface SidebarProps {
  sections: NavItem[];
  activeSection: string;
  onSelect: (id: string) => void;
  header?: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({ sections, activeSection, onSelect, header }) => (
  <aside className="sidebar-nav d-flex flex-column" style={{ minHeight: '100vh' }}>
    {header && <div className="px-3 py-3 border-bottom">{header}</div>}
    <nav className="flex-grow-1 py-2">
      {sections.map(item => (
        <button
          key={item.id}
          onClick={() => onSelect(item.id)}
          className={`sidebar-nav-item w-100 border-0 bg-transparent text-start ${activeSection === item.id ? 'active' : ''}`}
        >
          <span className="me-2">{item.icon}</span>
          <span className="flex-grow-1">{item.label}</span>
          {item.badge != null && item.badge > 0 && (
            <span className="badge bg-danger rounded-pill ms-auto" style={{ fontSize: '0.7rem' }}>
              {item.badge}
            </span>
          )}
        </button>
      ))}
    </nav>
  </aside>
);
