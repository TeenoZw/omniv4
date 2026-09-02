# 06 – Delivery Roadmap

This roadmap reflects the new Omni Logistics scope: customer onboarding, billing, support, and Wialon-based tracking access.

## Status Snapshot

| Phase | Name                              | Owner                   | Status        |
| ----- | --------------------------------- | ----------------------- | ------------- |
| 1     | Enquiry & Quotation Intake        | Admin / Platform        | 🔄 In progress |
| 2     | Admin Operations Dashboard        | Admin squad             | 🔄 In progress |
| 3     | Customer Portal & Login           | Client squad            | 🔄 In progress |
| 4     | Billing & Subscription Automation | Platform                | ⏳ Upcoming   |
| 5     | Support & Feedback Workflows      | Support                 | ⏳ Upcoming   |
| 6     | Partner Integrations (Wialon)     | Platform                | ⏳ Upcoming   |
| 7     | Hardening & Observability         | DevOps                  | ⏳ Upcoming   |
| 8     | Testing & Documentation           | All squads              | ⏳ Upcoming   |

## Phase Details

### Phase 1 – Enquiry & Quotation Intake

- Public landing with enquiry form (no hardware pricing).
- Capture plan type, hardware choices, and add-ons.
- Admin can quote, update status, and close deals.

### Phase 2 – Admin Operations Dashboard

- Enquiry review queue with filters and notes.
- Hub provisioning and account activation tooling.
- Billing status visibility and admin activity logs.

### Phase 3 – Customer Portal & Login

- Customer login for billing, subscriptions, support requests.
- Clear separation between Omni portal and Wialon tracking access.

### Phase 4 – Billing & Subscription Automation

- Subscription lifecycle (trial, active, overdue, suspended).
- Manual and automated invoices.
- Payment capture and receipts.

### Phase 5 – Support & Feedback Workflows

- Ticketing + feedback capture.
- SLA tracking for business customers.

### Phase 6 – Partner Integrations (Wialon)

- Wialon authentication handoff and tracking access.
- Data sync for asset mappings and operational visibility.

### Phase 7 – Hardening & Observability

- CI/CD, monitoring, audit trails, and backup workflows.

### Phase 8 – Testing & Documentation

- Regression suites for onboarding, billing, and admin workflows.
- Updated runbooks and customer-facing docs.

## Upcoming Milestones

1. **Enquiry MVP:** landing → enquiry → admin queue → quote status.
2. **Admin Portal MVP:** enquiries + hub provisioning + notes.
3. **Customer Portal MVP:** login + subscription view + support requests.

## References

- `docs/11_restructure_summary.md` – repository changes
- `docs/10_implementation_checklist.md` – granular deliverables
- `docs/09_quickstart.md` – environment setup
