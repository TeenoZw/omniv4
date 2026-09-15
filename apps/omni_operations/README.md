# Omni Operations

Fleet, telematics, tracker, SIM, maintenance, and customer operations for Omni Business Platform.

## Purpose

`omni_operations` is the custom Frappe app for the Omni v4 operating layer.

ERPNext owns the ERP backbone:

- Accounting
- Inventory
- Sales
- Purchasing
- Customers
- Suppliers
- Items
- Warehouses
- Invoices
- Payments

Omni Operations owns the fleet-specific workflows that make the platform different:

- Fleet vehicles
- Drivers
- Tracker profiles
- SIM profiles
- Tracker installations
- Telematics provider account/unit links
- Telematics sync logs
- Customer Fleet 360
- Fleet contracts
- Fleet maintenance work orders

## Current Evaluation Site

This app was scaffolded for the local Omni v4 evaluation bench:

```bash
cd /workspace/development/frappe-bench
bench --site development.localhost list-apps
```

Expected installed apps:

- `frappe`
- `erpnext`
- `omni_operations`

## Implementation Order

Start narrow:

1. Define modules.
2. Define roles.
3. Add fixtures for modules, roles, workspace, and custom fields.
4. Add core DocTypes one workflow at a time.
5. Link Omni DocTypes to ERPNext records instead of duplicating ERP data.

## Design Rule

Build simple operational screens on top of ERPNext's reliable transaction engine.

Do not expose the full ERPNext Desk to fleet operators or customers unless their role genuinely needs it.

## License

gpl-3.0
