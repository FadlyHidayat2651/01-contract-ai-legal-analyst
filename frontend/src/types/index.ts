export interface Contract {
  id: number;
  title?: string;
  filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  upload_date: string;
  processed: boolean;
  processing_status: string;
  risk_level?: string;
  total_pages?: number;
  word_count?: number;
  party_names?: string[];
  contract_date?: string;
  effective_date?: string;
  expiration_date?: string;
  contract_value?: number;
  currency?: string;
  created_at: string;
  updated_at: string;
}

export interface Clause {
  id: number;
  contract_id: number;
  title?: string;
  clause_type: string;
  content: string;
  page_number?: number;
  confidence_score: number;
  risk_level: string;
  risk_factors?: string[];
  analysis?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentSection {
  id: number;
  contract_id: number;
  title?: string;
  section_type: string;
  content: string;
  page_number?: number;
  order_index: number;
  confidence_score?: number;
  created_at: string;
}

export interface ContractStats {
  total_contracts: number;
  processed_contracts: number;
  pending_contracts: number;
  total_clauses: number;
  high_risk_clauses: number;
  critical_risk_clauses: number;
}

export interface ClauseTypeCount {
  clause_type: string;
  count: number;
}

export interface RiskDistribution {
  risk_level: string;
  count: number;
  percentage: number;
}

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type RiskLevel = 'critical' | 'high' | 'medium' | 'low';
export type ClauseType = 
  | 'payment_terms'
  | 'termination'
  | 'confidentiality'
  | 'liability'
  | 'intellectual_property'
  | 'dispute_resolution'
  | 'force_majeure'
  | 'warranties'
  | 'indemnification'
  | 'governing_law';

// Made with Bob
