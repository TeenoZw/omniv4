import { frappeCall } from "$lib/api/frappe";

export type EnquiryPayload = {
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
  fleet_segments: Array<{ vehicle_type: string; label: string; count: number }>;
  message?: string | null;
  terms_accepted: boolean;
  privacy_accepted: boolean;
};

export async function submitEnquiry(payload: EnquiryPayload) {
  return frappeCall<{ received: boolean; reference: string; message: string }>(
    "omni_operations.customer_portal.enquiries.submit_quote_request",
    { method: "POST", body: payload },
  );
}
