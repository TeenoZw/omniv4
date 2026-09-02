# Phase 4 – Admin Web App To-Do List

1. **Foundation & Tooling**
   1.1 Install Tailwind CSS, PostCSS, and shared design tokens that match the client portal.
   1.2 Add ESLint, Prettier, Vitest, and Testing Library configs; wire `npm run check` to lint + test.
   1.3 Define global layout scaffolding (App shell, navigation, responsive breakpoints) with dark/light theme variables.

2. **Authentication & Session Management**
   2.1 Implement FastAPI JWT login flow plus refresh handling (admin login is email + password only; hub codes stay exclusive to the client portals).
   2.2 Integrate role claims to determine Admin, Technician, Hub Manager, Client scopes.
   2.3 Build hub selector UI so users can switch between multiple hub memberships.
   2.4 Add route guards + session store (persisted) enforcing RBAC per view.

3. **Device Inventory Module**
   3.1 Create API clients for devices, pairing requests, and onboarding health.
   3.2 Build device list with filters (status, hub, model, last heartbeat) and pagination.
   3.3 Implement device detail drawer: metadata, linked vehicle, onboarding snapshots, support notes.
   3.4 Add CRUD flows: register device, edit status, decommission, export inventory CSV.
   3.5 Wire pairing wizard that triggers the pairing workflow (request → technician → admin approval).

4. **Hub & User Management**
   4.1 Hub overview page: plan badge (Individual/Business), active devices/vehicles counts, compliance checklist.
   4.2 Hub CRUD forms with validation + subscription metadata editing.
   4.3 User directory per hub with invite flow (email + role) and revoke actions.
   4.4 Role assignment UI showing stackable roles per hub and auditing changes.

5. **Technician Workflow Board**
   5.1 Fetch pairing tickets grouped by status; show SLA timers and assignment.
   5.2 Technician submission form capturing device, vehicle, hub, and notes (mobile-friendly).
   5.3 Admin action panel to approve/reject/return tickets with audit logging.
   5.4 Notifications (toasts + optional email hooks) when ticket status changes.

6. **Audit Logs & Activity Dashboard**
   6.1 Expose API client for audit events (user, hub, action, timestamp, payload diff).
   6.2 Build log viewer with search, filters, and JSON diff modal.
   6.3 Admin overview dashboard: cards for active hubs, pending tickets, device health, subscription mix.
   6.4 Export and download audit reports over selectable date ranges.

7. **Quality, Accessibility, and Testing**
   7.1 Add Vitest coverage for components, stores, and API utilities (target ≥80%).
   7.2 Include integration tests for workflow-critical paths (device add, pairing approval, role assignment).
   7.3 Run a11y checks (labels, keyboard nav, color contrast) across core pages.
   7.4 Validate responsive layout on desktop ≥1280px and tablet ≥768px.
   7.5 Prepare deployment checklist (build, preview, CI) for Phase 4 handoff.
