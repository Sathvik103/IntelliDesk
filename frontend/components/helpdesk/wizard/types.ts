export type WizardStep = 1 | 2 | 3 | 4 | 5 | 6;

export interface WizardFormData {
  // Step 1
  domainId: string;
  domainName: string;
  domainSlaHours: number;
  // Step 2
  issueId: string | null;
  issueTitle: string;
  isCustomIssue: boolean;
  // Step 3
  domainDetails: Record<string, unknown>;
  // Step 4
  locationData: {
    tower?: string;
    floor?: string;
    flat_number?: string;
    building?: string;
    department?: string;
    room?: string;
  };
  locationName: string;
  // Step 5
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT' | 'CRITICAL';
}

export const INITIAL_FORM_DATA: WizardFormData = {
  domainId: '',
  domainName: '',
  domainSlaHours: 24,
  issueId: null,
  issueTitle: '',
  isCustomIssue: false,
  domainDetails: {},
  locationData: {},
  locationName: '',
  priority: 'NORMAL',
};
