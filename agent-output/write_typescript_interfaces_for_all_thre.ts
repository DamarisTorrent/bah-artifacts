/**
 * Contractor Portal API Data Models
 * TypeScript interfaces for the three core data models
 */

// ============================================================================
// Contractor Model
// ============================================================================

/**
 * Address information for a contractor
 */
interface Address {
  street1: string;
  street2: string | null;
  city: string;
  /** 2-letter state code */
  state: string;
  zip: string;
  /** ISO 3166-1 alpha-2 country code */
  country: string;
}

/**
 * Contractor entity representing a federal contractor
 */
interface Contractor {
  /** UUID identifier */
  id: string;
  /** 5-character CAGE code */
  cage_code: string;
  /** 12-character Unique Entity Identifier */
  uei: string;
  legal_name: string;
  dba_name: string | null;
  status: 'active' | 'suspended' | 'debarred' | 'pending';
  business_type: 'small' | 'large' | 'sdvosb' | 'wosb' | '8a' | 'hubzone';
  naics_codes: string[];
  /** ISO 8601 date - SAM.gov registration expiration */
  sam_expiration: string;
  poc_name: string;
  poc_email: string;
  poc_phone: string;
  address: Address;
  /** ISO 8601 datetime */
  created_at: string;
  /** ISO 8601 datetime */
  updated_at: string;
}

// ============================================================================
// Task Order Model
// ============================================================================

/**
 * Period of performance for a task order
 */
interface PeriodOfPerformance {
  /** ISO 8601 date */
  start: string;
  /** ISO 8601 date */
  end: string;
}

/**
 * Contract Line Item Number (CLIN) details
 */
interface CLIN {
  clin_number: string;
  description: string;
  /** Fixed-price, time and materials, or cost-plus */
  type: 'ffp' | 't_and_m' | 'cost_plus';
  unit: string;
  quantity: number;
  unit_price: number;
  total: number;
}

/**
 * Task Order entity representing a government task order
 */
interface TaskOrder {
  /** UUID identifier */
  id: string;
  task_order_number: string;
  /** UUID reference to parent contract */
  contract_id: string;
  /** UUID reference to contractor */
  contractor_id: string;
  title: string;
  description: string;
  status: 'draft' | 'active' | 'completed' | 'cancelled';
  period_of_performance: PeriodOfPerformance;
  /** Maximum contract value in USD */
  ceiling_value: number;
  /** Currently obligated amount in USD */
  obligated_value: number;
  /** Total invoiced amount to date in USD */
  invoiced_to_date: number;
  /** Contract Line Item Numbers */
  clins: CLIN[];
  contracting_officer: string;
  cor_name: string;
  cor_email: string;
  /** ISO 8601 datetime */
  created_at: string;
  /** ISO 8601 datetime */
  updated_at: string;
}

// ============================================================================
// Invoice Model
// ============================================================================

/**
 * Line item on an invoice
 */
interface InvoiceLineItem {
  clin_number: string;
  description: string;
  /** Hours worked (for time and materials contracts) */
  hours: number | null;
  /** Hourly rate (for time and materials contracts) */
  rate: number | null;
  /** Line item amount in USD */
  amount: number;
}

/**
 * Invoice entity representing a contractor invoice submission
 */
interface Invoice {
  /** UUID identifier */
  id: string;
  invoice_number: string;
  /** UUID reference to task order */
  task_order_id: string;
  /** UUID reference to contractor */
  contractor_id: string;
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'paid';
  /** ISO 8601 date - start of billing period */
  period_start: string;
  /** ISO 8601 date - end of billing period */
  period_end: string;
  /** ISO 8601 date - when invoice was submitted */
  submission_date: string | null;
  /** ISO 8601 date - when payment was made */
  payment_date: string | null;
  line_items: InvoiceLineItem[];
  /** Subtotal amount in USD */
  subtotal: number;
  /** Tax amount in USD */
  tax: number;
  /** Total amount in USD */
  total: number;
  /** URLs to supporting documentation */
  supporting_documents: string[];
  /** Notes from reviewer (populated on rejection or approval) */
  reviewer_notes: string | null;
  /** ISO 8601 datetime */
  created_at: string;
  /** ISO 8601 datetime */
  updated_at: string;
}

// ============================================================================
// Export all interfaces
// ============================================================================

export type {
  Address,
  Contractor,
  PeriodOfPerformance,
  CLIN,
  TaskOrder,
  InvoiceLineItem,
  Invoice
};