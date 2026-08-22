'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  ShieldAlert,
  HardHat,
  Wrench,
  UserCheck,
  Building2,
  LogOut,
  LogIn,
  Layers,
  Sparkles,
} from 'lucide-react';

interface NavbarProps {
  onOpenAuth: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenAuth, activeTab, setActiveTab }) => {
  const { user, role, organization, allOrganizations, setOrganization, switchDemoRole, logout } = useAuth();
  const [switching, setSwitching] = useState<string | null>(null);

  const handleDemoSwitch = async (username: string) => {
    setSwitching(username);
    try {
      await switchDemoRole(username);
    } catch (e) {
      console.error(e);
    } finally {
      setSwitching(null);
    }
  };

  return (
    <header className="bg-white border-bottom shadow-sm sticky-top">
      {/* Top Demo Bar */}
      <div className="bg-dark text-white py-1 px-3 border-bottom small">
        <div className="container-fluid d-flex flex-wrap justify-content-between align-items-center gap-2">
          <div className="d-flex align-items-center gap-2 text-light">
            <Sparkles size={15} className="text-warning" />
            <span className="fw-semibold">Role Quick Switcher:</span>
            <span className="text-muted d-none d-md-inline">(Instant preview across all system roles)</span>
          </div>

          <div className="d-flex flex-wrap align-items-center gap-1">
            <button
              onClick={() => handleDemoSwitch('admin_greenwood')}
              disabled={switching !== null}
              className={`btn btn-sm py-0 px-2 rounded-pill ${
                user?.username === 'admin_greenwood' ? 'btn-primary' : 'btn-outline-light'
              }`}
            >
              <ShieldAlert size={13} className="me-1" />
              Colony Admin
            </button>

            <button
              onClick={() => handleDemoSwitch('emp_rajesh')}
              disabled={switching !== null}
              className={`btn btn-sm py-0 px-2 rounded-pill ${
                user?.username === 'emp_rajesh' ? 'btn-warning text-dark' : 'btn-outline-light'
              }`}
            >
              <ZapIcon size={13} className="me-1" />
              Electrician (Rajesh)
            </button>

            <button
              onClick={() => handleDemoSwitch('emp_suresh')}
              disabled={switching !== null}
              className={`btn btn-sm py-0 px-2 rounded-pill ${
                user?.username === 'emp_suresh' ? 'btn-info text-dark' : 'btn-outline-light'
              }`}
            >
              <Wrench size={13} className="me-1" />
              Plumber (Suresh)
            </button>

            <button
              onClick={() => handleDemoSwitch('resident_neha')}
              disabled={switching !== null}
              className={`btn btn-sm py-0 px-2 rounded-pill ${
                user?.username === 'resident_neha' ? 'btn-success' : 'btn-outline-light'
              }`}
            >
              <UserCheck size={13} className="me-1" />
              Resident (Neha)
            </button>

            <button
              onClick={() => handleDemoSwitch('superadmin')}
              disabled={switching !== null}
              className={`btn btn-sm py-0 px-2 rounded-pill ${
                user?.username === 'superadmin' ? 'btn-danger' : 'btn-outline-light'
              }`}
            >
              Super Admin
            </button>
          </div>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="container-fluid px-3 py-2">
        <div className="d-flex align-items-center justify-content-between">
          {/* Logo & Brand */}
          <div className="d-flex align-items-center gap-3">
            <div className="d-flex align-items-center gap-2">
              <div
                className="bg-primary text-white p-2 rounded-3 d-flex align-items-center justify-content-center shadow-sm"
                style={{ width: 38, height: 38 }}
              >
                <Layers size={22} />
              </div>
              <div>
                <h6 className="mb-0 fw-bold text-dark lh-1">IntelliDesk</h6>
                <small className="text-muted" style={{ fontSize: '0.72rem' }}>
                  Workforce Assignment SaaS
                </small>
              </div>
            </div>

            {/* Organization Selector */}
            {allOrganizations.length > 0 && (
              <div className="d-none d-lg-flex align-items-center ms-3 border-start ps-3">
                <Building2 size={16} className="text-muted me-2" />
                <select
                  className="form-select form-select-sm border-0 bg-light fw-medium text-dark"
                  style={{ width: 'auto', minWidth: 230, cursor: 'pointer' }}
                  value={organization?.id || ''}
                  onChange={(e) => {
                    const selected = allOrganizations.find((o) => o.id === e.target.value);
                    if (selected) setOrganization(selected);
                  }}
                >
                  {allOrganizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name} ({org.org_type_display || org.org_type})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* User Profile & Navigation */}
          <div className="d-flex align-items-center gap-2">
            {user ? (
              <div className="d-flex align-items-center gap-2">
                <div className="text-end d-none d-sm-block">
                  <div className="fw-semibold text-dark small lh-1">
                    {user.first_name ? `${user.first_name} ${user.last_name}` : user.username}
                  </div>
                  <span
                    className={`badge mt-1 ${
                      user.role === 'ADMIN'
                        ? 'bg-primary'
                        : user.role === 'EMPLOYEE'
                        ? 'bg-warning text-dark'
                        : 'bg-success'
                    }`}
                    style={{ fontSize: '0.68rem' }}
                  >
                    {user.role_display || user.role}
                  </span>
                </div>

                <button
                  onClick={logout}
                  className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1 ms-2"
                  title="Logout"
                >
                  <LogOut size={14} />
                  <span className="d-none d-md-inline">Logout</span>
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="btn btn-primary btn-sm d-flex align-items-center gap-1"
              >
                <LogIn size={15} />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

function ZapIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}
