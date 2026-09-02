# 04 – Schema Overview

This document outlines the core tables for the onboarding, billing, and support workflows.

## Core Tables

- **users**: Accounts, roles, authentication.
- **hubs**: Customer hubs and profile metadata.
- **hub_memberships**: User ↔ hub assignments and roles.
- **enquiries**: Customer requests, quote status, and admin notes.
- **subscriptions**: Billing and plan metadata per hub.

## Enquiries (Example)

```
CREATE TABLE enquiries (
  id UUID PRIMARY KEY,
  status enquiry_status NOT NULL,
  customer_type enquiry_customer_type NOT NULL,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  company_name TEXT,
  fleet_size TEXT,
  operating_area TEXT,
  preferred_contact_method TEXT,
  expected_go_live_date TIMESTAMPTZ,
  tracking_use_case TEXT,
  hardware_choices JSONB NOT NULL,
  add_ons JSONB NOT NULL,
  message TEXT,
  terms_accepted BOOLEAN NOT NULL,
  privacy_accepted BOOLEAN NOT NULL,
  quoted_monthly NUMERIC(10,2),
  quoted_hardware_total NUMERIC(10,2),
  quote_sent_at TIMESTAMPTZ,
  responded_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  admin_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
