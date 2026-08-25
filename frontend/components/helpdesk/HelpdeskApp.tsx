'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Navbar } from './Navbar';
import { AdminPortal } from './AdminPortal';
import { EmployeePortal } from './EmployeePortal';
import { ResidentPortal } from './ResidentPortal';
import { SuperAdminPortal } from './SuperAdminPortal';
import { CandidateInspectorModal } from './CandidateInspectorModal';
import { FeedbackModal } from './FeedbackModal';
import { AuthModal } from './AuthModal';
import { ServiceRequest } from '@/lib/types';
import { ShieldCheck, UserCheck, HardHat } from 'lucide-react';

export const HelpdeskApp: React.FC = () => {
  const { user, role, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('portal');
  const [inspectingRequestId, setInspectingRequestId] = useState<string | null>(null);
  const [feedbackRequest, setFeedbackRequest] = useState<ServiceRequest | null>(null);
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);

  if (isLoading) {
    return (
      <div className="d-flex flex-column align-items-center justify-content-center min-vh-100 bg-light">
        <div className="spinner-border text-primary mb-3" role="status" style={{ width: '3rem', height: '3rem' }}>
          <span className="visually-hidden">Loading IntelliDesk Platform...</span>
        </div>
        <h5 className="fw-bold text-dark mb-1">IntelliDesk Platform</h5>
        <p className="text-muted small">Initializing multi-tenant workforce engine...</p>
      </div>
    );
  }

  return (
    <div className="min-vh-100 d-flex flex-column bg-light">
      {/* Top Navbar & Role Switcher */}
      <Navbar
        onOpenAuth={() => setShowAuthModal(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Portal Content based on Role */}
      <main className="flex-grow-1">
        {user?.is_superuser ? (
          <SuperAdminPortal />
        ) : role === 'ADMIN' ? (
          <AdminPortal onInspectRequest={(reqId) => setInspectingRequestId(reqId)} />
        ) : role === 'EMPLOYEE' ? (
          <EmployeePortal />
        ) : (
          <ResidentPortal onOpenFeedback={(req) => setFeedbackRequest(req)} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-top py-3 mt-auto text-center small text-muted">
        <div className="container d-flex flex-wrap justify-content-between align-items-center gap-2">
          <div>
            <strong>IntelliDesk</strong> &copy; {new Date().getFullYear()} &mdash; Intelligent Helpdesk &amp; Automated Workforce Assignment
          </div>
          <div className="d-flex gap-3">
            <span>Privacy Policy</span>
            <span>&bull;</span>
            <span>Terms of Service</span>
            <span>&bull;</span>
            <span>Support</span>
          </div>
        </div>
      </footer>

      {/* Modals */}
      <CandidateInspectorModal
        requestId={inspectingRequestId}
        onClose={() => setInspectingRequestId(null)}
      />

      <FeedbackModal
        request={feedbackRequest}
        onClose={() => setFeedbackRequest(null)}
        onSubmitted={() => {
          // Trigger refresh where appropriate
        }}
      />

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </div>
  );
};
