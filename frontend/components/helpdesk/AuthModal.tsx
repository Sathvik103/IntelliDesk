'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiAuth } from '@/lib/api';
import { LogIn, UserPlus, Building2, Lock, User, Mail, Phone, AlertCircle } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { login, allOrganizations, organization } = useAuth();
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [firstName, setFirstName] = useState<string>('');
  const [lastName, setLastName] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [selectedOrgId, setSelectedOrgId] = useState<string>(organization?.id || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        await apiAuth.register({
          username,
          password,
          email,
          first_name: firstName,
          last_name: lastName,
          phone,
          organization: selectedOrgId || (allOrganizations[0]?.id || null),
        });
        await login(username, password);
      } else {
        await login(username, password);
      }
      onClose();
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.error ||
          err?.response?.data?.detail ||
          'Authentication failed. Please check your details.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal show d-block"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.6)', zIndex: 1050 }}
      tabIndex={-1}
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
          {/* Header */}
          <div className="modal-header bg-dark text-white border-0 py-3 px-4">
            <div className="d-flex align-items-center gap-2">
              {isRegister ? <UserPlus size={20} className="text-primary" /> : <LogIn size={20} className="text-primary" />}
              <h5 className="modal-title fw-bold mb-0">
                {isRegister ? 'Create SaaS Account' : 'Sign In to IntelliDesk'}
              </h5>
            </div>
            <button
              type="button"
              className="btn-close btn-close-white"
              onClick={onClose}
            />
          </div>

          <form onSubmit={handleSubmit}>
            <div className="modal-body p-4 bg-light">
              {error && (
                <div className="alert alert-danger py-2 small d-flex align-items-center gap-2 mb-3">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Toggle Register / Login */}
              <div className="btn-group w-100 mb-3" role="group">
                <button
                  type="button"
                  onClick={() => setIsRegister(false)}
                  className={`btn btn-sm ${!isRegister ? 'btn-primary fw-bold' : 'btn-outline-secondary'}`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => setIsRegister(true)}
                  className={`btn btn-sm ${isRegister ? 'btn-primary fw-bold' : 'btn-outline-secondary'}`}
                >
                  Register New
                </button>
              </div>

              {isRegister && (
                <div className="row g-2 mb-3">
                  <div className="col-6">
                    <label className="form-label small fw-semibold text-muted">First Name</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      placeholder="e.g. John"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="col-6">
                    <label className="form-label small fw-semibold text-muted">Last Name</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      placeholder="e.g. Doe"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div className="mb-3">
                <label className="form-label small fw-semibold text-muted">Username / ID</label>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-white">
                    <User size={14} className="text-muted" />
                  </span>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Enter username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>
              </div>

              {isRegister && (
                <div className="mb-3">
                  <label className="form-label small fw-semibold text-muted">Email Address</label>
                  <div className="input-group input-group-sm">
                    <span className="input-group-text bg-white">
                      <Mail size={14} className="text-muted" />
                    </span>
                    <input
                      type="email"
                      className="form-control"
                      placeholder="name@organization.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>
              )}

              <div className="mb-3">
                <label className="form-label small fw-semibold text-muted">Password</label>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-white">
                    <Lock size={14} className="text-muted" />
                  </span>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              {isRegister && (
                <>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold text-muted">Organization</label>
                    <select
                      className="form-select form-select-sm"
                      value={selectedOrgId}
                      onChange={(e) => setSelectedOrgId(e.target.value)}
                    >
                      {allOrganizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-semibold text-muted">Role</label>
                    <select
                      className="form-select form-select-sm"
                      value={role}
                      onChange={(e) => setRole(e.target.value as any)}
                    >
                      <option value="USER">Resident / Customer</option>
                      <option value="EMPLOYEE">Workforce Technician</option>
                      <option value="ADMIN">Facility Administrator</option>
                    </select>
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer bg-white border-top px-4 py-3">
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm px-3"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary btn-sm px-4 fw-semibold"
                disabled={loading}
              >
                {loading ? 'Processing...' : isRegister ? 'Register & Enter' : 'Sign In'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
