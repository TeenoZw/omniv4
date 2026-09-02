# 43 - Omni v4 Portal API and Session Strategy

## Purpose

This document defines how the Svelte customer portal should talk to Frappe/ERPNext.

The goal is to avoid carrying the old v3 FastAPI auth/API shape into Omni v4.

## Decision

The customer portal will call narrow Omni/Frappe API methods.

It will not call:

- old FastAPI `/api/v1` routes
- broad ERPNext Desk routes
- generic document APIs without server-side customer scoping

## Recommended API Base

Local:

```text
http://development.localhost:8000/api/method
```

Production:

```text
https://admin.omnilogistics.co.zw/api/method
```

If a reverse proxy is added for same-site portal API calls, the public route may become:

```text
https://www.omnilogistics.co.zw/api/method
```

That proxy should forward to Frappe without exposing Desk as the customer experience.

## Session Strategy

### Preferred Production Strategy

Use Frappe session authentication through a controlled same-site proxy where possible:

```text
www.omnilogistics.co.zw/portal
www.omnilogistics.co.zw/api/method -> Frappe API upstream
```

Benefits:

- simpler browser cookie behavior
- less CORS complexity
- public website and portal feel like one product

### Acceptable Cross-Subdomain Strategy

If the API remains on `admin.omnilogistics.co.zw`, configure:

- allowed origins for `www.omnilogistics.co.zw`
- credentials/cookie policy
- CSRF handling
- HTTPS only
- strict customer portal method allowlist

## Authentication Model

Portal users are Frappe users with the `Customer Portal User` role and Omni customer/hub scoping.

Minimum requirements:

1. User can log in.
2. API can identify the current Frappe user.
3. API can resolve the user's allowed customer/hub scope.
4. Every portal endpoint applies that scope on the server.
5. Customer users cannot see other customers' records.
6. Customer users should not land in Desk as their primary experience.

## Initial Endpoint Contract

All endpoint names are proposed under:

```text
omni_operations.customer_portal.api
```

### Current User

Method:

```text
omni_operations.customer_portal.api.get_current_customer
```

Optional input for internal staff/testing only:

```json
{
  "customer": "H2O Hub"
}
```

Portal users are always scoped by their linked customer. A customer value sent by a portal user's browser must not override server-side scope.

Returns:

```json
{
  "user": {
    "email": "customer@example.com",
    "full_name": "Customer User"
  },
  "customer": {
    "name": "H2O Hub",
    "display_name": "H2O Hub"
  },
  "roles": ["Customer Portal User"]
}
```

### Dashboard Summary

Method:

```text
omni_operations.customer_portal.api.get_dashboard_summary
```

Optional internal/testing input:

```json
{
  "customer": "H2O Hub"
}
```

Returns:

```json
{
  "vehicles": {
    "total": 12,
    "online": 10,
    "offline": 2
  },
  "invoices": {
    "outstanding_total": 250.0,
    "overdue_count": 1
  },
  "support": {
    "open_tickets": 2
  },
  "documents": {
    "expiring_soon": 1
  }
}
```

### Vehicles

Method:

```text
omni_operations.customer_portal.api.get_vehicles
```

Optional internal/testing input:

```json
{
  "customer": "H2O Hub"
}
```

Returns:

```json
{
  "vehicles": [
    {
      "name": "Fleet Vehicle-0001",
      "registration_number": "AHG 9216",
      "display_name": "Nissan X-Trail",
      "status": "Active",
      "latest_telematics": {
        "provider": "Wialon",
        "last_seen": "2026-08-19T08:00:00Z",
        "speed": 0,
        "latitude": -17.8252,
        "longitude": 31.0335
      }
    }
  ]
}
```

### Vehicle Detail

Method:

```text
omni_operations.customer_portal.api.get_vehicle_detail
```

Required input:

```json
{
  "vehicle": "Fleet Vehicle-0001"
}
```

Optional internal/testing input:

```json
{
  "customer": "H2O Hub"
}
```

Returns:

```json
{
  "vehicle": {},
  "telematics": {},
  "maintenance": [],
  "documents": [],
  "support_tickets": []
}
```

### Invoices

Method:

```text
omni_operations.customer_portal.api.get_invoices
```

Optional internal/testing input:

```json
{
  "customer": "H2O Hub"
}
```

Returns:

```json
{
  "invoices": [
    {
      "name": "ACC-SINV-2026-00001",
      "posting_date": "2026-08-19",
      "due_date": "2026-08-26",
      "status": "Unpaid",
      "grand_total": 100.0,
      "outstanding_amount": 100.0,
      "fiscalisation_status": "Pending"
    }
  ]
}
```

### Documents

Method:

```text
omni_operations.customer_portal.api.get_documents
```

Optional internal/testing input:

```json
{
  "customer": "H2O Hub"
}
```

Returns:

```json
{
  "documents": [
    {
      "name": "DOC-0001",
      "title": "Vehicle Registration",
      "document_type": "Registration",
      "vehicle": "Fleet Vehicle-0001",
      "expires_on": "2027-08-19",
      "file_url": "/private/files/example.pdf"
    }
  ]
}
```

### Support Tickets

Methods:

```text
omni_operations.customer_portal.api.get_support_tickets
omni_operations.customer_portal.api.create_support_ticket
```

Optional internal/testing input:

```json
{
  "customer": "H2O Hub"
}
```

Returns:

```json
{
  "tickets": [
    {
      "name": "ISS-0001",
      "subject": "Tracker offline",
      "status": "Open",
      "priority": "Medium",
      "created_on": "2026-08-19T08:00:00Z"
    }
  ]
}
```

## Error Shape

Portal API methods should return clear errors and avoid leaking internal tracebacks.

Recommended shape:

```json
{
  "ok": false,
  "error": {
    "code": "not_permitted",
    "message": "You do not have access to this record."
  }
}
```

## Security Rules

1. Every endpoint must resolve customer scope server-side.
2. Never trust a customer id sent from the browser.
3. Vehicle detail endpoints must confirm that the vehicle belongs to the current user's customer scope.
4. Invoice endpoints must filter by the current user's customer scope.
5. Document endpoints must not expose private files from unrelated customers.
6. Telematics endpoints must never expose provider tokens or raw credentials.
7. Support creation must set customer/user ownership server-side.
8. Desk access and portal access should be treated separately.

## Svelte Migration Notes

The current `client-web` API layer still contains old v3 assumptions:

- `/users/login`
- `/auth/refresh`
- `/auth/logout`
- `/hubs/current/*`

These should be replaced or isolated behind a new Omni v4 portal API client.

Recommended next implementation step:

1. Add the Frappe portal API methods.
2. Add a small `client-web` Frappe API client.
3. Move portal routes to the new client.
4. Remove or clearly mark old v3 API clients as legacy.
