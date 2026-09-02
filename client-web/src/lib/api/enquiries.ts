import { apiFetch } from "$lib/api/http";

export type EnquiryPayload = {
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
};

export async function submitEnquiry(payload: EnquiryPayload) {
  const response = await apiFetch("/enquiries", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Unable to submit enquiry");
  }

  return response.json();
}
