export type EnquiryStatus =
  | "new"
  | "quoted"
  | "awaiting_payment"
  | "onboarded"
  | "closed_lost";

export type Enquiry = {
  id: string;
  status: EnquiryStatus;
  customer_type: "individual" | "business";
  full_name: string;
  email: string;
  phone: string;
  company_name?: string | null;
  fleet_size?: string | null;
  operating_area?: string | null;
  preferred_contact_method?: string | null;
  expected_go_live_date?: string | null;
  tracking_use_case?: string | null;
  hardware_choices: string[];
  add_ons: string[];
  message?: string | null;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  quoted_monthly?: number | null;
  quoted_hardware_total?: number | null;
  quote_sent_at?: string | null;
  responded_at?: string | null;
  closed_at?: string | null;
  admin_notes?: string | null;
  created_at: string;
  updated_at: string;
};
