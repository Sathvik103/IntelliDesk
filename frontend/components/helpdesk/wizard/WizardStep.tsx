'use client';

import React from 'react';

interface WizardStepProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

export const WizardStep: React.FC<WizardStepProps> = ({ title, description, children }) => (
  <section>
    <h6 className="fw-bold mb-1">{title}</h6>
    <p className="text-muted small mb-3">{description}</p>
    {children}
  </section>
);
