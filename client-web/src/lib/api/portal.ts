import { frappeCall } from "$lib/api/frappe";

const PORTAL_API = "omni_operations.customer_portal.api";

export type PortalCurrentCustomer = {
  user: {
    email: string;
    full_name: string;
  };
  customer: {
    name: string;
    display_name: string;
  };
  roles: string[];
};

export type PortalDashboardSummary = {
  customer: {
    name: string;
    display_name: string;
  };
  vehicles: {
    total: number;
    online: number;
    offline: number;
  };
  invoices: {
    outstanding_total: number;
    open_count: number;
  };
  support: {
    open_tickets: number;
  };
  documents: {
    total: number;
    expiring_soon: number;
  };
  maintenance: {
    open: number;
  };
};

export type PortalVehicle = {
  name: string;
  registration_number: string;
  display_name: string;
  vehicle_type?: string | null;
  status?: string | null;
  make?: string | null;
  model?: string | null;
  year?: number | null;
  odometer?: number | null;
  latest_telematics?: {
    provider?: string | null;
    status?: string | null;
    sync_enabled: boolean;
    unit_name?: string | null;
    last_seen?: string | null;
    last_sync_status?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    speed?: number | null;
    ignition: boolean;
    odometer?: number | null;
  } | null;
};

export type PortalInvoice = {
  name: string;
  posting_date?: string | null;
  due_date?: string | null;
  status?: string | null;
  grand_total?: number | null;
  outstanding_amount?: number | null;
  fiscalisation_status?: string | null;
};

export type PortalDocument = {
  name: string;
  title?: string | null;
  document_type?: string | null;
  status?: string | null;
  vehicle?: string | null;
  issue_date?: string | null;
  expires_on?: string | null;
  reference_number?: string | null;
  file_url?: string | null;
};

export type PortalTicket = {
  name: string;
  subject: string;
  status?: string | null;
  priority?: string | null;
  created_on?: string | null;
  modified?: string | null;
};

export async function fetchPortalCurrentCustomer() {
  return frappeCall<PortalCurrentCustomer>(`${PORTAL_API}.get_current_customer`);
}

export async function fetchPortalDashboardSummary() {
  return frappeCall<PortalDashboardSummary>(`${PORTAL_API}.get_dashboard_summary`);
}

export async function fetchPortalVehicles() {
  return frappeCall<{ vehicles: PortalVehicle[] }>(`${PORTAL_API}.get_vehicles`);
}

export async function fetchPortalInvoices() {
  return frappeCall<{ invoices: PortalInvoice[] }>(`${PORTAL_API}.get_invoices`);
}

export async function fetchPortalDocuments() {
  return frappeCall<{ documents: PortalDocument[] }>(`${PORTAL_API}.get_documents`);
}

export async function fetchPortalSupportTickets() {
  return frappeCall<{ tickets: PortalTicket[] }>(`${PORTAL_API}.get_support_tickets`);
}

export async function createPortalSupportTicket(payload: {
  subject: string;
  description?: string;
  priority?: "Low" | "Medium" | "High" | "Urgent";
}) {
  return frappeCall<{ name: string; status: string }>(`${PORTAL_API}.create_support_ticket`, {
    method: "POST",
    body: payload,
  });
}
