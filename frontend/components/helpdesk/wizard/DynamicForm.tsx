'use client';

import React from 'react';
import { FieldDef } from '@/lib/domainForms';

interface DynamicFormProps {
  fields: FieldDef[];
  value: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({ fields, value, onChange }) => {
  const update = (name: string, nextValue: unknown) => onChange({ ...value, [name]: nextValue });

  return <div className="row g-3">{fields.map((field) => {
    const fieldValue = value[field.name];
    return <div className={field.type === 'textarea' ? 'col-12' : 'col-md-6'} key={field.name}>
      {field.type === 'boolean' ? (
        <label className="form-check form-switch pt-2">
          <input className="form-check-input" type="checkbox" checked={Boolean(fieldValue)} onChange={(e) => update(field.name, e.target.checked)} />
          <span className="form-check-label small">{field.label}</span>
        </label>
      ) : <>
        <label className="form-label small fw-medium">{field.label}{field.required && <span className="text-danger"> *</span>}</label>
        {field.type === 'select' ? (
          <select className="form-select form-select-sm" value={String(fieldValue || '')} onChange={(e) => update(field.name, e.target.value)}>
            <option value="">Select…</option>{field.options?.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        ) : field.type === 'textarea' ? (
          <textarea className="form-control form-control-sm" rows={3} placeholder={field.placeholder} value={String(fieldValue || '')} onChange={(e) => update(field.name, e.target.value)} />
        ) : (
          <input className="form-control form-control-sm" type={field.type} placeholder={field.placeholder} value={String(fieldValue || '')} onChange={(e) => update(field.name, e.target.value)} />
        )}
      </>}
    </div>;
  })}</div>;
};
