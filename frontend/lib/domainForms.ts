export type FieldType = 'text' | 'number' | 'boolean' | 'textarea' | 'select';

export interface FieldDef {
  name: string;
  label: string;
  type: FieldType;
  options?: string[];
  placeholder?: string;
  required?: boolean;
}

export type DomainFormDefs = Record<string, FieldDef[]>;

export const domainFormDefs: DomainFormDefs = {
  'Electrical': [
    { name: 'affected_equipment', label: 'Affected Equipment', type: 'text', placeholder: 'e.g. ceiling fan, socket', required: true },
    { name: 'affected_room', label: 'Affected Room', type: 'text', placeholder: 'e.g. bedroom, kitchen', required: true },
    { name: 'power_available', label: 'Is power available?', type: 'boolean' },
    { name: 'burning_smell', label: 'Burning smell present?', type: 'boolean' },
    { name: 'sparks', label: 'Sparks observed?', type: 'boolean' },
    { name: 'when_started', label: 'When did it start?', type: 'text', placeholder: 'e.g. this morning, yesterday' },
    { name: 'safety_concern', label: 'Safety concern?', type: 'boolean' },
    { name: 'description', label: 'Additional Details', type: 'textarea', placeholder: 'Describe the issue in detail' },
  ],
  'Plumbing': [
    { name: 'fixture', label: 'Fixture', type: 'select', options: ['Tap', 'Shower', 'Toilet', 'Basin', 'Pipeline', 'Water Heater', 'Other'] },
    { name: 'severity', label: 'Severity', type: 'select', options: ['Minor Drip', 'Moderate Leak', 'Major Leak', 'Burst Pipe'] },
    { name: 'water_flowing', label: 'Is water still flowing?', type: 'boolean' },
    { name: 'water_supply_affected', label: 'Is water supply affected?', type: 'boolean' },
    { name: 'affected_room', label: 'Affected Room', type: 'text', placeholder: 'e.g. bathroom, kitchen' },
    { name: 'when_started', label: 'When did it start?', type: 'text' },
    { name: 'description', label: 'Additional Details', type: 'textarea' },
  ],
  'HVAC / AC': [
    { name: 'ac_type', label: 'AC Type', type: 'select', options: ['Split', 'Window', 'Central', 'Portable'] },
    { name: 'room', label: 'Room', type: 'text', required: true },
    { name: 'cooling_severity', label: 'Cooling Issue', type: 'select', options: ['Not cooling', 'Cooling insufficiently', 'Overcooling', 'No power'] },
    { name: 'leakage', label: 'Water leakage?', type: 'boolean' },
    { name: 'noise', label: 'Unusual noise?', type: 'boolean' },
    { name: 'smell', label: 'Unusual smell?', type: 'boolean' },
    { name: 'when_started', label: 'When did it start?', type: 'text' },
    { name: 'description', label: 'Additional Details', type: 'textarea' },
  ],
  'Cleaning': [
    { name: 'area_type', label: 'Area Type', type: 'select', options: ['Flat/Apartment', 'Common Area', 'Parking', 'Garden', 'Rooftop', 'Lobby'] },
    { name: 'approximate_size', label: 'Approximate Size (sq ft)', type: 'number' },
    { name: 'cleaning_type', label: 'Cleaning Type', type: 'select', options: ['Regular', 'Deep Clean', 'Post-construction', 'Pest Control', 'Sanitation'] },
    { name: 'preferred_time', label: 'Preferred Time', type: 'select', options: ['Morning (8am–12pm)', 'Afternoon (12pm–4pm)', 'Evening (4pm–8pm)', 'Flexible'] },
    { name: 'special_requirements', label: 'Special Requirements', type: 'text' },
    { name: 'description', label: 'Additional Details', type: 'textarea' },
  ],
  'Carpentry': [
    { name: 'furniture_item', label: 'Furniture/Item', type: 'text', required: true },
    { name: 'damage_problem', label: 'Damage/Problem', type: 'select', options: ['Broken', 'Loose', 'Misaligned', 'Squeaking', 'Missing part', 'Other'] },
    { name: 'material', label: 'Material', type: 'select', options: ['Wood', 'Plywood', 'MDF', 'Laminate', 'Metal', 'Other'] },
    { name: 'severity', label: 'Severity', type: 'select', options: ['Minor', 'Moderate', 'Severe'] },
    { name: 'location_detail', label: 'Location Detail', type: 'text' },
    { name: 'description', label: 'Additional Details', type: 'textarea' },
  ],
  'Security': [
    { name: 'incident_type', label: 'Incident Type', type: 'select', options: ['CCTV Malfunction', 'Gate/Door Issue', 'Access Control', 'Suspicious Activity', 'Intercom Fault', 'Other'] },
    { name: 'location_detail', label: 'Location', type: 'text', required: true },
    { name: 'incident_time', label: 'Incident Time', type: 'text', placeholder: 'e.g. 2pm today' },
    { name: 'safety_concern', label: 'Immediate safety concern?', type: 'boolean' },
    { name: 'description', label: 'Description', type: 'textarea', required: true },
  ],
  'IT Support': [
    { name: 'device', label: 'Device', type: 'select', options: ['Desktop', 'Laptop', 'Printer', 'Phone', 'Network Equipment', 'Server', 'Other'] },
    { name: 'os', label: 'Operating System', type: 'select', options: ['Windows', 'macOS', 'Linux', 'Android', 'iOS', 'N/A'] },
    { name: 'hardware_or_software', label: 'Type', type: 'select', options: ['Hardware', 'Software', 'Network', 'Both'] },
    { name: 'problem_type', label: 'Problem Type', type: 'text', required: true },
    { name: 'error_description', label: 'Error/Message', type: 'textarea' },
    { name: 'when_started', label: 'When did it start?', type: 'text' },
    { name: 'location_detail', label: 'Location', type: 'text' },
    { name: 'description', label: 'Additional Details', type: 'textarea' },
  ],
  'General Maintenance': [
    { name: 'asset_item', label: 'Asset/Item', type: 'text', required: true },
    { name: 'problem_category', label: 'Problem Category', type: 'select', options: ['Broken', 'Worn out', 'Damaged', 'Not functioning', 'Maintenance overdue', 'Other'] },
    { name: 'location_detail', label: 'Location', type: 'text', required: true },
    { name: 'when_started', label: 'When noticed?', type: 'text' },
    { name: 'description', label: 'Additional Details', type: 'textarea' },
  ],
};

export function getDomainFormDefs(domainName: string): FieldDef[] {
  return domainFormDefs[domainName] ?? domainFormDefs['General Maintenance'];
}
