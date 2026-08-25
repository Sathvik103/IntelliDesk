'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, ChevronLeft, ChevronRight, MapPin, X } from 'lucide-react';
import { apiRequests, apiServices } from '@/lib/api';
import { getDomainColors, getPriorityColors } from '@/lib/colors';
import { getDomainFormDefs } from '@/lib/domainForms';
import { PriorityType, PredefinedIssue, ServiceDomain } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { DynamicForm } from './DynamicForm';
import { INITIAL_FORM_DATA, WizardFormData, WizardStep as Step } from './types';
import { WizardStep } from './WizardStep';

interface RequestWizardProps { onClose: () => void; onSuccess: () => void; }
const STEP_META = [['Service', 'Choose a service category'], ['Problem', 'Select the problem'], ['Details', 'Tell us what happened'], ['Location', 'Where is the issue?'], ['Priority', 'How urgent is it?'], ['Review', 'Confirm your request']] as const;
const priorities: Array<{ value: PriorityType; label: string; note: string }> = [
  { value: 'LOW', label: 'Low', note: 'Convenience repair' }, { value: 'NORMAL', label: 'Normal', note: 'Standard service' }, { value: 'HIGH', label: 'High', note: 'Impacts daily routine' }, { value: 'URGENT', label: 'Urgent', note: 'Outage or safety concern' }, { value: 'CRITICAL', label: 'Critical', note: 'Emergency / hazard' },
];

export const RequestWizard: React.FC<RequestWizardProps> = ({ onClose, onSuccess }) => {
  const { organization, user } = useAuth();
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [formData, setFormData] = useState<WizardFormData>({ ...INITIAL_FORM_DATA, locationName: user?.address || '' });
  const [domains, setDomains] = useState<ServiceDomain[]>([]);
  const [issues, setIssues] = useState<PredefinedIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const selectedDomain = useMemo(() => domains.find((domain) => domain.id === formData.domainId), [domains, formData.domainId]);

  useEffect(() => { apiServices.listDomains().then((data) => setDomains(data.filter((domain) => domain.is_active))).catch(() => setError('Unable to load service categories.')).finally(() => setLoading(false)); }, []);
  useEffect(() => { if (!formData.domainId) return; apiServices.listIssues(formData.domainId).then(setIssues).catch(() => setIssues(selectedDomain?.predefined_issues || [])); }, [formData.domainId, selectedDomain?.predefined_issues]);

  const update = (patch: Partial<WizardFormData>) => setFormData((previous) => ({ ...previous, ...patch }));
  const composeLocation = (data: WizardFormData['locationData']) => Object.values(data).filter(Boolean).join(', ');
  const requiredDetailsComplete = getDomainFormDefs(formData.domainName).filter((field) => field.required).every((field) => Boolean(formData.domainDetails[field.name]));
  const canAdvance = () => currentStep === 1 ? Boolean(formData.domainId) : currentStep === 2 ? Boolean(formData.issueId || formData.isCustomIssue) : currentStep === 3 ? requiredDetailsComplete : currentStep === 4 ? Boolean(formData.locationName.trim()) : true;
  const next = () => { if (canAdvance()) setCurrentStep((currentStep + 1) as Step); };
  const previous = () => currentStep === 1 ? onClose() : setCurrentStep((currentStep - 1) as Step);
  const selectDomain = (domain: ServiceDomain) => update({ domainId: domain.id, domainName: domain.name, domainSlaHours: domain.sla_hours, issueId: null, issueTitle: '', isCustomIssue: false, domainDetails: {} });
  const selectIssue = (issue: PredefinedIssue | null) => update({ issueId: issue?.id || null, issueTitle: issue?.title || 'Other / custom issue', isCustomIssue: !issue, priority: issue?.default_priority || formData.priority });
  const submit = async () => { setSubmitting(true); setError(null); try { await apiRequests.create({ domain: formData.domainId, predefined_issue: formData.isCustomIssue ? null : formData.issueId, custom_description: JSON.stringify(formData.domainDetails), details_snapshot: formData.domainDetails, location_name: formData.locationName, priority: formData.priority, latitude: organization?.latitude ?? 0, longitude: organization?.longitude ?? 0 }); setSuccess(true); window.setTimeout(onSuccess, 1100); } catch (caught: any) { setError(caught?.response?.data?.detail || 'Could not submit this request. Please try again.'); } finally { setSubmitting(false); } };
  const locationFields = organization?.org_type === 'OFFICE_SPACE' ? [['building', 'Building'], ['floor', 'Floor'], ['department', 'Department'], ['room', 'Room']] : [['tower', 'Tower'], ['floor', 'Floor'], ['flat_number', 'Flat number'], ['room', 'Room']];

  return <div className="modal show d-block" style={{ backgroundColor: 'rgba(15, 23, 42, .6)', zIndex: 1055 }} role="dialog" aria-modal="true"><div className="modal-dialog modal-fullscreen-sm-down modal-dialog-centered" style={{ maxWidth: 680 }}><div className="modal-content border-0 shadow-lg" style={{ borderRadius: 16 }}>
    <div className="modal-header border-0 px-4 pt-4 pb-2"><div><h5 className="fw-bold mb-1">New Service Request</h5><p className="small text-muted mb-0">{STEP_META[currentStep - 1][1]}</p></div><button className="btn btn-link text-muted p-1" onClick={onClose} aria-label="Close"><X size={20} /></button></div>
    <div className="px-4 pb-3 d-flex gap-1">{STEP_META.map(([label], index) => <div key={label} className="flex-fill"><div className="rounded-pill" style={{ height: 5, background: index < currentStep ? 'var(--color-primary)' : 'var(--color-border)' }} /><span className="d-none d-sm-block text-muted mt-1" style={{ fontSize: '.64rem' }}>{index + 1}. {label}</span></div>)}</div>
    <div className="modal-body px-4 pb-3" style={{ minHeight: 330 }}>{success ? <div className="text-center py-5"><CheckCircle2 className="text-success mb-3" size={52} /><h6 className="fw-bold">Request submitted</h6><p className="text-muted small">We’re assigning the best available technician.</p></div> : <>
      {error && <div className="alert alert-danger small py-2 d-flex gap-2"><AlertCircle size={16} />{error}</div>}
      {currentStep === 1 && <WizardStep title="What do you need help with?" description="Choose the service category that best fits.">{loading ? <div className="spinner-border spinner-border-sm" /> : <div className="row g-2">{domains.map((domain) => { const color = getDomainColors(domain.name); const chosen = formData.domainId === domain.id; return <div className="col-sm-6" key={domain.id}><button className="w-100 rounded-3 p-3 text-start" style={{ border: `1px solid ${chosen ? color.border : 'var(--color-border)'}`, backgroundColor: chosen ? color.bg : 'white', color: chosen ? color.text : 'var(--color-text-primary)' }} onClick={() => selectDomain(domain)}><div className="fw-semibold small">{domain.name}</div><div className="small opacity-75 mt-1">{domain.description || `${domain.sla_hours} hour SLA`}</div></button></div>; })}</div>}</WizardStep>}
      {currentStep === 2 && <WizardStep title="Select the problem" description="Choose a common issue or add your own."><div className="d-grid gap-2">{issues.map((issue) => <button key={issue.id} onClick={() => selectIssue(issue)} className={`text-start rounded-3 p-3 ${formData.issueId === issue.id ? 'border-primary bg-primary bg-opacity-10' : 'border bg-white'}`}><div className="fw-semibold small">{issue.title}</div><div className="small text-muted mt-1">Default priority: {issue.default_priority_display || issue.default_priority}</div></button>)}<button onClick={() => selectIssue(null)} className={`text-start rounded-3 p-3 ${formData.isCustomIssue ? 'border-primary bg-primary bg-opacity-10' : 'border bg-white'}`}><div className="fw-semibold small">Other / custom issue</div></button></div></WizardStep>}
      {currentStep === 3 && <WizardStep title="Add the details" description="This helps the technician arrive prepared."><DynamicForm fields={getDomainFormDefs(formData.domainName)} value={formData.domainDetails} onChange={(domainDetails) => update({ domainDetails })} /></WizardStep>}
      {currentStep === 4 && <WizardStep title="Where is the issue?" description="Add the precise location so we can reach you quickly."><div className="row g-3">{locationFields.map(([key, label]) => <div className="col-sm-6" key={key}><label className="form-label small fw-medium">{label}</label><input className="form-control form-control-sm" value={String(formData.locationData[key as keyof WizardFormData['locationData']] || '')} onChange={(event) => { const locationData = { ...formData.locationData, [key]: event.target.value }; update({ locationData, locationName: composeLocation(locationData) }); }} /></div>)}</div><div className="mt-3"><label className="form-label small fw-medium d-flex gap-1"><MapPin size={14} />Location summary</label><input className="form-control form-control-sm" value={formData.locationName} onChange={(event) => update({ locationName: event.target.value })} placeholder="Location or unit" /></div></WizardStep>}
      {currentStep === 5 && <WizardStep title="Set the priority" description="Choose the urgency level that best reflects the impact."><div className="d-grid gap-2">{priorities.map((priority) => { const color = getPriorityColors(priority.value); const chosen = formData.priority === priority.value; return <button key={priority.value} onClick={() => update({ priority: priority.value })} className="rounded-3 p-3 text-start" style={{ border: `1px solid ${chosen ? color.border : 'var(--color-border)'}`, background: chosen ? color.bg : 'white' }}><span className="fw-semibold small" style={{ color: color.text }}>{priority.label}</span><span className="text-muted small ms-2">{priority.note}</span></button>; })}</div></WizardStep>}
      {currentStep === 6 && <WizardStep title="Review your request" description="Check the details before sending."><div className="border rounded-3 overflow-hidden small">{[['Service', formData.domainName], ['Problem', formData.issueTitle], ['Location', formData.locationName], ['Priority', formData.priority]].map(([label, value]) => <div className="d-flex px-3 py-2 border-bottom" key={label}><span className="text-muted" style={{ minWidth: 100 }}>{label}</span><span className="fw-medium">{value}</span></div>)}<div className="px-3 py-2"><span className="text-muted d-block mb-1">Details</span>{Object.entries(formData.domainDetails).filter(([, value]) => value !== '' && value !== false).map(([key, value]) => <span className="badge text-bg-light me-1 mb-1" key={key}>{key.replaceAll('_', ' ')}: {String(value)}</span>)}</div></div></WizardStep>}
    </>}</div>
    {!success && <div className="modal-footer border-0 px-4 pb-4 pt-2 d-flex justify-content-between"><button className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1" onClick={previous} disabled={submitting}><ChevronLeft size={15} />{currentStep === 1 ? 'Cancel' : 'Back'}</button>{currentStep < 6 ? <button className="btn btn-primary btn-sm d-flex align-items-center gap-1" onClick={next} disabled={!canAdvance()}>Next<ChevronRight size={15} /></button> : <button className="btn btn-success btn-sm" onClick={submit} disabled={submitting}>{submitting ? 'Submitting…' : 'Submit request'}</button>}</div>}
  </div></div></div>;
};
