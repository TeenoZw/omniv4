import { frappeCall } from "$lib/api/frappe";

const QUOTE_ADD_ON_API = "omni_operations.omni_setup.quote_add_ons";

export type QuoteAddOnStatus = "Available" | "Out of Stock" | "Coming Soon" | "Inactive";

export type PublicQuoteAddOn = {
  add_on_id: string;
  display_name: string;
  status: QuoteAddOnStatus;
  is_enabled: boolean;
  public_note?: string | null;
};

export async function getPublicQuoteAddOns() {
  return frappeCall<{ add_ons: PublicQuoteAddOn[] }>(`${QUOTE_ADD_ON_API}.get_public_quote_add_ons`);
}
