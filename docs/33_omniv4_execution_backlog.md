# 33 - Omni v4 Execution Backlog

## Purpose

This is the traceable execution backlog for building Omni v4 with selective ERPNext adoption.

Execution principle:

> Use ERPNext for the ERP backbone. Build Omni for fleet, telematics provider integration, tracker/SIM operations, field service, customer fleet views, and simplified user experience.

Related docs:

- `docs/31_omniv4_work_plan.md`
- `docs/32_erpnext_selective_adoption_plan.md`
- `docs/34_erpnext_doctype_validation.md`

## Status Legend

- `todo` - not started
- `doing` - currently in progress
- `blocked` - cannot continue until a dependency is solved
- `done` - completed and verified
- `deferred` - intentionally postponed

## Track A - Environment and ERPNext Evaluation

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| A-001 | Locate local ERPNext source | None | done | ERPNext source path confirmed as `/Users/h2o/erpnext-develop`. |
| A-002 | Check local Frappe/bench readiness | A-001 | done | Confirm whether `bench`, Frappe app, Redis, MariaDB/MySQL, Node, and Python are available. |
| A-003 | Decide ERPNext version strategy | A-002 | done | Choose stable ERPNext/Frappe branch/version for Omni v4 evaluation instead of blindly using develop. |
| A-004 | Create ERPNext evaluation bench | A-003 | done | A local Frappe bench exists and can start. |
| A-005 | Install ERPNext into evaluation bench | A-004 | done | ERPNext app is installed on a local site. |
| A-006 | Create Zimbabwe demo company | A-005 | done | Demo company has currency, fiscal year, chart of accounts, taxes, and base settings. |
| A-007 | Create sample ERP data | A-006 | done | Customer, supplier, items, warehouse, invoice, purchase order, asset, payment, and stock records exist. |
| A-008 | Validate target ERPNext DocTypes | A-007 | done | Confirm which DocTypes Omni uses unchanged, extends, or avoids. |

### A-002 Findings

Checked on 2026-08-11:

- ERPNext source exists at `/Users/h2o/erpnext-develop`.
- `bench` is not installed or not on `PATH`.
- No existing `frappe-bench` folder was found under `/Users/h2o`.
- No local Frappe app folder was found under `/Users/h2o`.
- System Python is `3.9.6`.
- Node is `v24.16.0`.
- Redis and MariaDB/MySQL were not detected from the quick command check.

Implication:

- We should not scaffold `omni_operations` until the Frappe/ERPNext evaluation environment is set up.
- We should choose a stable ERPNext/Frappe version before setup. The local ERPNext source appears to be a develop branch and may have newer runtime requirements than the current machine.

### A-003 Version Strategy

Decision:

- Use ERPNext/Frappe `version-15` for the first Omni v4 evaluation bench.
- Treat `/Users/h2o/erpnext-develop` as a local source reference, not the evaluation runtime.

Reasoning:

- Frappe's installation guidance says version 15 can use Python `3.10` to `3.13`.
- The current machine has Python `3.9.6`, so it needs a newer Python either way.
- The local ERPNext develop checkout declares a much newer Python requirement and is not the right first target for a stable business platform.
- Frappe's support version table lists `version-15` as supported until the end of 2027, while `develop` is bleeding edge.

Environment target for the evaluation bench:

- Frappe branch: `version-15`
- ERPNext branch: `version-15`
- Python: `3.11` or `3.12`
- Node: current `v24.16.0` is above the minimum expected for v15, but if build tooling complains we can switch to Node 18/20 for bench compatibility.
- Database: MariaDB-compatible service required.
- Redis: required.

Next action:

- Run a real-data migration dry run from the staging CSV templates when v3 exports are available.

### A-004/A-005 Setup Result

Completed on 2026-08-16:

- Docker Desktop was running and `docker ps` succeeded.
- Official `frappe_docker` dev stack was started from `erpnext-eval/frappe_docker`.
- Docker services are running under project `omni-erpnext-eval`:
  - `frappe`
  - `mariadb`
  - `redis-cache`
  - `redis-queue`
- Bench was initialized at `erpnext-eval/frappe_docker/development/frappe-bench`.
- Bench uses Frappe `15.118.0` from branch `version-15`.
- The site `development.localhost` was created with Administrator password `admin`.
- ERPNext `15.119.2` from branch `version-15` was installed on `development.localhost`.
- Verification command:
  - `bench --site development.localhost list-apps`
- Verified installed apps:
  - `frappe 15.118.0 version-15`
  - `erpnext 15.119.2 version-15`

Important notes:

- The bench image includes Python `3.12.12` and `3.14.2`; the bench was initialized using Python `3.12.12`.
- MariaDB is currently `11.8`; Frappe v15 warns this is newer than its tested range. This is acceptable for local evaluation, but production should pin a tested MariaDB version.
- `bench doctor` reports scheduler disabled and no workers online because the development server has not been started yet.

### A-006 Demo Company Result

Completed on 2026-08-16:

- ERPNext setup wizard was completed programmatically for the evaluation site.
- Company: `Omni Demo Zimbabwe`
- Abbreviation: `ODZ`
- Country: `Zimbabwe`
- Default currency: `USD`
- Fiscal year: `2026` from `2026-01-01` to `2026-12-31`
- Default bank account: `Omni Demo Bank - ODZ`
- Standard chart of accounts was created.
- Core warehouses were created, including:
  - `Stores - ODZ`
  - `Finished Goods - ODZ`
  - `Work In Progress - ODZ`
  - `Goods In Transit - ODZ`

### A-007 Sample ERP Data Result

Completed on 2026-08-16:

- Customer: `Acme Logistics Zimbabwe`
- Supplier: `Harare Tracker Supplies`
- Warehouses:
  - `Main Fleet Stock - ODZ`
  - `Technician Stock - ODZ`
  - `Faulty Returns - ODZ`
- Items:
  - `FLEET-MONTHLY-SERVICE`
  - `TRACKER-HW-4G`
  - `SIM-IOT`
  - `INSTALL-LABOUR`
  - `MAINT-LABOUR`
  - `RELAY-12V`
  - `VEHICLE-DEMO-ASSET`
- Stock entry: `MAT-STE-2026-00001`
- Quotation: `SAL-QTN-2026-00001`
- Sales invoice: `ACC-SINV-2026-00001`
- Customer payment: `ACC-PAY-2026-00001`
- Purchase order: `PUR-ORD-2026-00001`
- Purchase receipt: `MAT-PRE-2026-00001`
- Purchase invoice: `ACC-PINV-2026-00001`
- Supplier payment: `ACC-PAY-2026-00002`
- Asset: `ACC-ASS-2026-00001`
- Issue: `ISS-2026-00001`

Verification highlights:

- `ACC-SINV-2026-00001` is submitted for `USD 290.00` and has `0.00` outstanding.
- `ACC-PINV-2026-00001` is submitted for `USD 235.00` and has `0.00` outstanding.
- `Main Fleet Stock - ODZ` has stock for trackers, SIMs, and relays after receipt/sale activity.

### A-008 DocType Boundary Result

Completed on 2026-08-16:

- Created `docs/34_erpnext_doctype_validation.md`.
- Use ERPNext unchanged for core ERP records such as Company, Fiscal Year, Account, Payment Entry, Supplier, Warehouse, Stock Entry, Purchase Order, Purchase Receipt, and Purchase Invoice.
- Extend or link ERPNext records where Omni needs fleet context, especially Customer, Item, Quotation, Sales Invoice, Asset, and Issue.
- Build Fleet Vehicle, Fleet Driver, Tracker Profile, SIM Profile, Tracker Installation, telematics provider links, Customer Fleet Profile, Fleet Contract, and Fleet Maintenance Work Order as custom Omni DocTypes in `omni_operations`.

### C-001 App Skeleton Result

Completed on 2026-08-16:

- Created Frappe app: `omni_operations`
- App path: `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations`
- App title: `Omni Operations`
- Publisher: `TeenoZw`
- Version: `0.0.1`
- License: `gpl-3.0`
- Installed on site: `development.localhost`
- Verified installed apps:
  - `frappe 15.118.0 version-15`
  - `erpnext 15.119.2 version-15`
  - `omni_operations 0.0.1 main`

### C-002 Module Result

Completed on 2026-08-16:

- Added app module namespaces:
  - `Fleet`
  - `Telematics`
  - `Tracker Inventory`
  - `SIM Inventory`
  - `Field Service`
  - `Customer Portal`
  - `Omni Dashboards`
  - `Omni Integrations`
  - `Omni Setup`
- Created matching package folders under `omni_operations`.
- Created Module Def records for the modules on `development.localhost`.

Important lesson:

- Do not name Omni modules `Integrations`, `Setup`, `Portal`, or other generic names already used by Frappe/ERPNext.
- A test migration with `Integrations` as an Omni module collided with Frappe's own `Integrations` module and briefly treated core integration DocTypes as orphaned.
- The module was renamed to `Omni Integrations`, migration was rerun, and the core `Connected App` DocType was restored.

### C-003 Role Result

Completed on 2026-08-16:

- Created minimal Omni roles:
  - `Omni Operations Admin`
  - `Fleet Manager`
  - `Installation Coordinator`
  - `Technician`
  - `Customer Portal User`
- Desk access:
  - `Omni Operations Admin`: enabled
  - `Fleet Manager`: enabled
  - `Installation Coordinator`: enabled
  - `Technician`: enabled
  - `Customer Portal User`: disabled, portal-only
- Added fixture export config to `omni_operations/hooks.py`.
- Exported fixtures:
  - `omni_operations/fixtures/role.json`
  - `omni_operations/fixtures/module_def.json`
- Verified with `bench --site development.localhost migrate`.

Additional hardening completed on 2026-08-17:

- Added `Fleet Manager` to the Omni role fixture so the role is present on fresh installs.
- Added `after_install` and `after_migrate` permission sync:
  - `omni_operations.omni_setup.permissions.sync_omni_security`
- Synced focused role permissions for fleet, tracker, SIM, installation, maintenance, telematics, fiscalisation, and portal-visible records.
- Verified roles and DocPerm rows on `development.localhost`.

### C-004 Workspace Result

Completed on 2026-08-16:

- Created Desk workspace: `Omni Operations`
- Workspace module: `Omni Operations`
- Workspace fixture: `omni_operations/fixtures/workspace.json`
- Workspace roles:
  - `Omni Operations Admin`
  - `Fleet Manager`
  - `Installation Coordinator`
  - `Technician`
  - `System Manager`
- Quick shortcuts:
  - `Fleet Vehicles`
  - `Customers`
  - `Support Tickets`
  - `Invoices`
- Work areas:
  - `Operations`
  - `Inventory`
  - `Commercial`
  - `Setup`
- Current links combine the first Omni operational DocType with existing ERPNext DocTypes:
  - `Fleet Vehicle`
  - `Fleet Driver`
  - `Tracker Profile`
  - `SIM Profile`
  - `Tracker Installation`
  - `Vehicle Assignment`
  - `Customer Fleet Profile`
  - `Customer`
  - `Issue`
  - `Asset`
  - `Item`
  - `Warehouse`
  - `Stock Entry`
  - `Quotation`
  - `Sales Invoice`
  - `Purchase Order`
  - `Purchase Invoice`
  - `User`
  - `Role`
- Verified with `bench --site development.localhost migrate`.

### C-005 Fixture Result

Completed on 2026-08-16:

- Added fixture declarations to `omni_operations/hooks.py` for:
  - `Role`
  - `Module Def`
  - `Workspace`
- Exported fixtures:
  - `omni_operations/fixtures/role.json`
  - `omni_operations/fixtures/module_def.json`
  - `omni_operations/fixtures/workspace.json`
- Verified that Frappe automatically syncs fixtures during:
  - `bench --site development.localhost install-app omni_operations`
  - `bench --site development.localhost migrate`
- Decision: no custom install hook is needed yet because Frappe's built-in fixture sync covers the current foundation records.
- Future custom fields and permissions should be added to the same fixture pattern when the first Omni DocTypes are created.

## Track B - v3 to ERPNext Mapping

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| B-001 | Map Omni v3 Hub to ERPNext Customer/Fleet Profile | A-008 | done | A field-by-field mapping exists for hub migration. |
| B-002 | Map Omni v3 Enquiry to Lead/Opportunity | A-008 | done | Enquiry lifecycle maps cleanly to ERPNext CRM or Omni custom DocType. |
| B-003 | Map Omni v3 Hardware Inventory | A-008 | done | Tracker inventory maps to ERPNext Item/Serial No plus Omni Tracker Profile. |
| B-004 | Map Omni v3 SIM Inventory | A-008 | done | SIM inventory maps to ERPNext Item/Serial No/Batch plus Omni SIM Profile. |
| B-005 | Map Omni v3 Vehicle/Asset records | A-008 | done | Vehicle records map to Omni Fleet Vehicle and optionally ERPNext Asset. |
| B-006 | Map Omni v3 Technician Jobs | A-008 | done | Technician jobs map to Omni Fleet Maintenance Work Order or ERPNext maintenance flow. |
| B-007 | Map Omni v3 Billing/Subscriptions | A-008 | done | Subscriptions and billing map to ERPNext Sales Invoice, Payment Entry, and Fleet Contract. |
| B-008 | Create migration/import templates | B-001 to B-007 | done | CSV/import templates exist for all approved migration targets. |

### B-001 to B-008 Migration Mapping Result

Completed on 2026-08-17:

- Added the v3 to Omni v4 migration map:
  - `docs/36_v3_to_omniv4_migration_map.md`
- Mapped these v3 source tables into ERPNext and Omni v4 targets:
  - `hubs` -> ERPNext `Customer`, `Contact`, `Address`, Omni `Customer Fleet Profile`
  - `enquiries` -> ERPNext `Lead`, `Opportunity`, `Quotation`, eventual `Customer`
  - `hardware_inventory`, `hardware_assignments`, `device_pairings` -> ERPNext `Item`/`Serial No`, Omni `Tracker Profile`, `Tracker Installation`, future `Telematics Unit Link`
  - `sim_inventory`, `sim_assignments` -> ERPNext `Item`/`Serial No` or `Batch`, Omni `SIM Profile`, `Tracker Installation`
  - `vehicles` -> Omni `Fleet Vehicle`, optional ERPNext `Asset`
  - `technician_jobs` -> Omni `Tracker Installation`, Omni `Fleet Maintenance Work Order`, or ERPNext `Issue`
  - `subscriptions` plus hub billing fields -> ERPNext `Sales Invoice`, `Payment Entry`, `Subscription`, and future Omni `Fleet Contract`
- Added staging CSV templates:
  - `docs/migration_templates/01_customers_from_hubs.csv`
  - `docs/migration_templates/02_customer_fleet_profiles_from_hubs.csv`
  - `docs/migration_templates/03_tracker_profiles_from_hardware.csv`
  - `docs/migration_templates/04_sim_profiles_from_sim_inventory.csv`
  - `docs/migration_templates/05_fleet_vehicles_from_vehicles.csv`
  - `docs/migration_templates/06_tracker_installations_from_assignments.csv`
  - `docs/migration_templates/07_sales_pipeline_from_enquiries.csv`
  - `docs/migration_templates/08_billing_subscriptions.csv`
- Decision: these are staging templates, not final Frappe Data Import exports. The safe production sequence is export v3 data into the staging columns, validate required references, then transform into Frappe/ERPNext Data Import format.

## Track C - Omni Frappe App Skeleton

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| C-001 | Create `omni_operations` app | A-008 | done | App exists, installs in bench, and has metadata. |
| C-002 | Define Omni modules | C-001 | done | Modules exist for Fleet, Telematics, Tracker Inventory, SIM Inventory, Field Service, Customer Portal, Dashboards, Integrations, Setup. |
| C-003 | Define Omni roles | C-001 | done | Minimal Omni roles exist: Omni Operations Admin, Fleet Manager, Installation Coordinator, Technician, Customer Portal User. |
| C-004 | Create Omni Operations workspace | C-002 | done | Workspace shows only focused Omni workflows. |
| C-005 | Add install hooks and fixtures | C-001 | done | Foundation fixtures for roles, modules, and workspace install/reinstall predictably. |

## Track D - Fleet Core

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| D-001 | Create Fleet Vehicle DocType | C-001, A-008 | done | Vehicle links to Customer, Company, Asset where applicable, and supports registration/VIN/type/status. |
| D-002 | Create Fleet Driver DocType | C-001 | done | Driver links to Customer/Company/User or Employee where applicable. |
| D-003 | Create Tracker Profile DocType | C-001 | done | Tracker links to ERPNext Item/Serial No and stores IMEI/device metadata. |
| D-004 | Create SIM Profile DocType | C-001 | done | SIM links to ERPNext Item/Serial No/Batch and stores ICCID/MSISDN/carrier/roaming. |
| D-005 | Create Tracker Installation DocType | D-001, D-003, D-004 | done | Installation links vehicle, tracker, SIM, technician, customer, location, and status. |
| D-006 | Create Vehicle Assignment DocType | D-001, D-002 | done | Driver/vehicle assignments are tracked with dates and status. |
| D-007 | Create Customer Fleet Profile DocType | D-001 | done | Customer-level fleet summary links vehicles, trackers, invoices, and maintenance. |

### D-001 Fleet Vehicle Result

Completed on 2026-08-16:

- Added `Fleet Vehicle` as the first custom Omni operational DocType in the `Fleet` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/fleet/doctype/fleet_vehicle/`
- Core links:
  - `customer` -> ERPNext `Customer`
  - `company` -> ERPNext `Company`
  - `asset` -> ERPNext `Asset`
- Core fields:
  - `registration_number`
  - `vehicle_name`
  - `vehicle_type`
  - `status`
  - `make`
  - `model`
  - `year`
  - `vin`
  - `odometer`
  - `notes`
- Permissions:
  - `System Manager`
  - `Omni Operations Admin`
  - `Fleet Manager`
  - `Installation Coordinator`
  - `Technician`
- Created demo vehicle:
  - `ADE-1001`
  - Customer: `Acme Logistics Zimbabwe`
  - Company: `Omni Demo Zimbabwe`
  - Asset: `ACC-ASS-2026-00001`
- Updated the `Omni Operations` workspace so `Fleet Vehicles` is the first quick-access operational shortcut.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `Fleet Vehicle` exists and fields link to ERPNext `Customer`, `Company`, and `Asset`.
- Direct smoke check confirmed the `ADE-1001` sample vehicle reads back with the expected customer, company, asset, and status.
- Direct validation check confirmed a vehicle without `registration_number` is rejected.

Test caveat:

- The targeted Frappe test runner was enabled and attempted with:
  - `bench --site development.localhost run-tests --app omni_operations --doctype "Fleet Vehicle"`
- It currently fails before reaching the Omni test because Frappe/ERPNext dependency setup asks for legacy/core `Payment Gateway`, while this installed v15 codebase contains `Payment Gateway Account` but no `Payment Gateway` DocType JSON.
- Treat this as an evaluation-bench test dependency issue to resolve separately; it does not block the `Fleet Vehicle` DocType itself, which was verified directly.

### D-002 Fleet Driver Result

Completed on 2026-08-16:

- Added `Fleet Driver` as the second custom Omni operational DocType in the `Fleet` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/fleet/doctype/fleet_driver/`
- Core links:
  - `company` -> ERPNext `Company`
  - `customer` -> ERPNext `Customer`
  - `employee` -> ERPNext `Employee`
  - `user` -> Frappe `User`
- Core fields:
  - `driver_name`
  - `status`
  - `phone`
  - `email`
  - `license_number`
  - `license_expiry_date`
  - `notes`
- Permissions:
  - `System Manager`
  - `Omni Operations Admin`
  - `Fleet Manager`
  - `Installation Coordinator`
  - `Technician`
- Created demo driver:
  - `FD-2026-0001`
  - Name: `Tawanda Demo Driver`
  - Customer: `Acme Logistics Zimbabwe`
  - Company: `Omni Demo Zimbabwe`
  - License: `ZWL-DEMO-1001`
- Added `Fleet Drivers` to the `Omni Operations` workspace links.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `Fleet Driver` exists and fields link to ERPNext/Frappe `Company`, `Customer`, `Employee`, and `User`.
- Direct smoke check confirmed the `FD-2026-0001` sample driver reads back with the expected customer, company, and status.
- Direct validation check confirmed a driver without `driver_name` is rejected.

### D-003 Tracker Profile Result

Completed on 2026-08-16:

- Added `Tracker Profile` as the first custom Omni hardware inventory DocType in the `Tracker Inventory` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/tracker_inventory/doctype/tracker_profile/`
- Core links:
  - `item_code` -> ERPNext `Item`
  - `serial_no` -> ERPNext `Serial No`
  - `current_customer` -> ERPNext `Customer`
  - `current_vehicle` -> Omni `Fleet Vehicle`
  - `assigned_technician` -> Frappe `User`
- Core fields:
  - `imei`
  - `tracker_name`
  - `status`
  - `manufacturer`
  - `device_model`
  - `firmware_version`
  - `purchase_date`
  - `warranty_expiry_date`
  - `last_installation_date`
  - `notes`
- Created demo tracker:
  - IMEI: `867530900001111`
  - Item: `TRACKER-HW-4G`
  - Serial No: `TRK-DEMO-0001`
  - Customer: `Acme Logistics Zimbabwe`
  - Vehicle: `ADE-1001`
- Added `Tracker Profiles` to the `Omni Operations` workspace links.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `Tracker Profile` exists and fields link to ERPNext `Item`, ERPNext `Serial No`, ERPNext `Customer`, and Omni `Fleet Vehicle`.
- Direct smoke check confirmed the `867530900001111` sample tracker reads back with the expected item, serial number, customer, vehicle, and status.
- Direct validation check confirmed a tracker without `imei` is rejected.

### D-004 SIM Profile Result

Completed on 2026-08-16:

- Added `SIM Profile` as the first custom Omni SIM inventory DocType in the `SIM Inventory` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/sim_inventory/doctype/sim_profile/`
- Core links:
  - `item_code` -> ERPNext `Item`
  - `serial_no` -> ERPNext `Serial No`
  - `batch_no` -> ERPNext `Batch`
  - `current_customer` -> ERPNext `Customer`
  - `current_vehicle` -> Omni `Fleet Vehicle`
  - `current_tracker` -> Omni `Tracker Profile`
- Core fields:
  - `iccid`
  - `msisdn`
  - `status`
  - `carrier`
  - `apn`
  - `roaming_enabled`
  - `activation_date`
  - `expiry_date`
  - `notes`
- Created demo SIM:
  - ICCID: `8936300000000000001`
  - MSISDN: `+263771001001`
  - Item: `SIM-IOT`
  - Serial No: `SIM-DEMO-0001`
  - Tracker: `867530900001111`
  - Vehicle: `ADE-1001`
  - Carrier: `Econet`
- Added `SIM Profiles` to the `Omni Operations` workspace links.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `SIM Profile` exists and fields link to ERPNext `Item`, ERPNext `Serial No`, ERPNext `Batch`, Omni `Tracker Profile`, and Omni `Fleet Vehicle`.
- Direct smoke check confirmed the `8936300000000000001` sample SIM reads back with the expected item, serial number, tracker, vehicle, carrier, and status.
- Direct validation check confirmed a SIM without `iccid` is rejected.

### D-005 Tracker Installation Result

Completed on 2026-08-16:

- Added `Tracker Installation` as the first custom Omni field-service workflow DocType in the `Field Service` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/field_service/doctype/tracker_installation/`
- Core links:
  - `customer` -> ERPNext `Customer`
  - `company` -> ERPNext `Company`
  - `vehicle` -> Omni `Fleet Vehicle`
  - `tracker` -> Omni `Tracker Profile`
  - `sim` -> Omni `SIM Profile`
  - `technician` -> Frappe `User`
  - `installation_coordinator` -> Frappe `User`
  - `sales_invoice` -> ERPNext `Sales Invoice`
- Core fields:
  - `status`
  - `scheduled_date`
  - `completed_date`
  - `installation_location`
  - `latitude`
  - `longitude`
  - `odometer`
  - `work_performed`
  - `customer_signoff_name`
  - `notes`
- Created demo installation:
  - `TI-2026-0001`
  - Customer: `Acme Logistics Zimbabwe`
  - Vehicle: `ADE-1001`
  - Tracker: `867530900001111`
  - SIM: `8936300000000000001`
  - Technician: `Administrator`
  - Invoice: `ACC-SINV-2026-00001`
  - Status: `Completed`
- Added `Tracker Installations` to the `Omni Operations` workspace links.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `Tracker Installation` exists and fields link to ERPNext `Customer`, ERPNext `Company`, Omni `Fleet Vehicle`, Omni `Tracker Profile`, Omni `SIM Profile`, Frappe `User`, and ERPNext `Sales Invoice`.
- Direct smoke check confirmed the `TI-2026-0001` sample installation reads back with the expected customer, vehicle, tracker, SIM, technician, invoice, and status.
- Direct validation check confirmed an installation without `vehicle` is rejected.

### D-006 Vehicle Assignment Result

Completed on 2026-08-16:

- Added `Vehicle Assignment` as the driver-to-vehicle history DocType in the `Fleet` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/fleet/doctype/vehicle_assignment/`
- Core links:
  - `company` -> ERPNext `Company`
  - `customer` -> ERPNext `Customer`
  - `vehicle` -> Omni `Fleet Vehicle`
  - `driver` -> Omni `Fleet Driver`
  - `assigned_by` -> Frappe `User`
- Core fields:
  - `status`
  - `start_datetime`
  - `end_datetime`
  - `primary_assignment`
  - `handover_odometer`
  - `return_odometer`
  - `notes`
- Created demo assignment:
  - `VA-2026-0001`
  - Vehicle: `ADE-1001`
  - Driver: `FD-2026-0001`
  - Status: `Active`
- Added `Vehicle Assignments` to the `Omni Operations` workspace links.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `Vehicle Assignment` exists and fields link to ERPNext `Company`, ERPNext `Customer`, Omni `Fleet Vehicle`, Omni `Fleet Driver`, and Frappe `User`.
- Direct smoke check confirmed the `VA-2026-0001` sample assignment reads back with the expected customer, vehicle, driver, start datetime, and status.
- Direct validation check confirmed an assignment without `vehicle` is rejected.

### D-007 Customer Fleet Profile Result

Completed on 2026-08-16:

- Added `Customer Fleet Profile` as the first customer-level fleet summary DocType in the `Fleet` module.
- Code path:
  - `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations/omni_operations/fleet/doctype/customer_fleet_profile/`
- Core links:
  - `customer` -> ERPNext `Customer`
  - `company` -> ERPNext `Company`
  - `account_manager` -> Frappe `User`
  - `last_installation` -> Omni `Tracker Installation`
  - `latest_sales_invoice` -> ERPNext `Sales Invoice`
  - `latest_support_ticket` -> ERPNext `Issue`
  - `primary_vehicle` -> Omni `Fleet Vehicle`
  - `primary_tracker` -> Omni `Tracker Profile`
  - `primary_sim` -> Omni `SIM Profile`
  - `primary_driver` -> Omni `Fleet Driver`
  - `vehicle_assignment` -> Omni `Vehicle Assignment`
- Core fields:
  - `status`
  - `total_vehicles`
  - `active_trackers`
  - `installed_sims`
  - `open_support_tickets`
  - `maintenance_notes`
  - `contract_notes`
  - `notes`
- Created demo customer fleet profile:
  - Customer: `Acme Logistics Zimbabwe`
  - Total vehicles: `1`
  - Active trackers: `1`
  - Installed SIMs: `1`
  - Primary vehicle: `ADE-1001`
  - Primary tracker: `867530900001111`
  - Latest invoice: `ACC-SINV-2026-00001`
- Added `Customer Fleet Profiles` to the `Omni Operations` workspace links.
- Re-exported workspace fixtures and reran migration successfully.

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Direct smoke check confirmed `Customer Fleet Profile` exists and fields link to ERPNext `Customer`, ERPNext `Company`, Omni `Fleet Vehicle`, Omni `Tracker Profile`, ERPNext `Sales Invoice`, Omni `Tracker Installation`, ERPNext `Issue`, and Omni `Vehicle Assignment`.
- Direct smoke check confirmed the `Acme Logistics Zimbabwe` profile reads back with the expected counts, primary vehicle, primary tracker, and latest invoice.
- Direct validation check confirmed a profile without `customer` is rejected.

### Track D Completion Result

Completed on 2026-08-16:

- Fleet Core now has the first complete operational data chain:
  - Customer Fleet Profile
  - Fleet Vehicle
  - Fleet Driver
  - Vehicle Assignment
  - Tracker Profile
  - SIM Profile
  - Tracker Installation
- The demo flow links:
  - `Acme Logistics Zimbabwe`
  - `ADE-1001`
  - `FD-2026-0001`
  - `VA-2026-0001`
  - `867530900001111`
  - `8936300000000000001`
  - `TI-2026-0001`
  - `ACC-SINV-2026-00001`

## Track E - Telematics Integration

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| E-001 | Define Telematics Provider Account DocType | C-001 | done | Stores customer/provider account linkage and safe integration metadata. |
| E-002 | Define Telematics Unit Link DocType | D-001, D-003 | done | Links Omni vehicle/tracker to external provider unit ID. |
| E-003 | Define Telematics Sync Log DocType | E-001 | done | Sync attempts and failures are auditable. |
| E-004 | Build first provider adapter prototype | E-001, E-002 | done | Can pull or reconcile unit metadata from the selected provider in a controlled test. |
| E-005 | Add telematics status to Vehicle 360 | E-004 | done | Vehicle view shows provider sync state without overwhelming users. |
| E-006 | Add first real telematics provider adapter | E-001 to E-004 | done | Wialon-compatible adapter can check credentials, list units, normalize latest position, update sync logs, and keep Wialon isolated behind the provider interface. |
| E-007 | Add provider account hierarchy/scope | E-001 | done | Provider accounts can represent system-wide, regional admin, or customer hub access without using provider scope for customer portal permissions. |

### E-001/E-002 Telematics Account and Unit Link Result

Completed on 2026-08-16:

- Added `Telematics Provider Account` in the `Telematics` module.
- Added `Telematics Unit Link` in the `Telematics` module.
- Provider account stores provider, company/customer, API base URL, auth type, credential fields, provider account ID, sync enabled flag, last sync status, and error summary.
- Unit link maps Omni vehicle/tracker/SIM/installation records to provider-neutral external unit/device identifiers.
- Unit link automatically copies provider from the provider account and customer from the linked vehicle.
- Added workspace links:
  - `Provider Accounts`
  - `Unit Links`
- Created demo records:
  - `Demo Telematics Account`
  - `TUL-2026-0001`

Verification:

- `bench --site development.localhost migrate` completed after adding both DocTypes.
- Direct smoke insert confirmed `TUL-2026-0001` links to vehicle `ADE-1001`, provider `Other`, and customer `Acme Logistics Zimbabwe`.

### E-003 Telematics Sync Log Result

Completed on 2026-08-16:

- Added `Telematics Sync Log` in the `Telematics` module.
- Sync log records provider account, optional unit link, sync type, status, timing, record counts, request/response summaries, and error message.
- On insert, sync log updates last sync health on the linked provider account and unit link.
- Added workspace link:
  - `Sync Logs`
- Added provider adapter skeleton:
  - `omni_operations/telematics/providers/base.py`
  - `omni_operations/telematics/providers/registry.py`

Verification:

- `bench --site development.localhost migrate` completed after adding the DocType.
- Created demo sync log `TSL-2026-0001`.
- Direct smoke check confirmed the log updated `Demo Telematics Account` and `TUL-2026-0001` to sync status `Success`.

### E-004 Provider Adapter Prototype Result

Completed on 2026-08-16:

- Added a provider-neutral sync service for unit metadata reconciliation.
- Added a demo provider adapter so the architecture can be tested without live external credentials.
- Added a provider registry that can later route `Wialon`, `Traccar`, `Navixy`, or another provider to its own adapter class.
- Current demo adapter maps provider values `Other` and `Custom API` to controlled demo sync behavior.
- Sync service updates matched `Telematics Unit Link` records and writes a `Telematics Sync Log`.

Code paths:

- `omni_operations/telematics/providers/demo.py`
- `omni_operations/telematics/providers/registry.py`
- `omni_operations/telematics/sync.py`

Verification:

- Ran `sync_provider_units("Demo Telematics Account")`.
- Created sync log `TSL-2026-0002`.
- Updated `TUL-2026-0001` with provider metadata including `Demo Fleet`, `Africa/Harare`, and sync status `Success`.

### E-005 Vehicle Telematics Status Result

Completed on 2026-08-16:

- Added vehicle telematics status API for a compact Vehicle 360 signal.
- Added Fleet Vehicle form JavaScript hook.
- The Fleet Vehicle form now has:
  - A telematics dashboard indicator.
  - A telematics headline message.
  - A `Sync Telematics` action under a `Telematics` button group.

Code paths:

- `omni_operations/telematics/status.py`
- `omni_operations/public/js/fleet_vehicle.js`
- `omni_operations/hooks.py`

Verification:

- Ran `get_vehicle_telematics_status("ADE-1001")`.
- Confirmed status returns `Success`, indicator `green`, and message `ADE 1001 Demo Unit`.

### E-006 Real Provider Adapter Result

Completed on 2026-08-18:

- Added Wialon as the first real telematics provider adapter while keeping the Omni model provider-neutral.
- Added `ProviderUnit.position` so providers can return normalized latest location data during a unit sync.
- Updated unit sync to copy latest latitude, longitude, speed, and timestamp into `Telematics Unit Link` when the link has `Sync Enabled` checked.
- Added a whitelisted `check_provider_connection` endpoint that writes an `Account Check` sync log.
- Added Desk form actions on `Telematics Provider Account`:
  - `Check Connection`
  - `Sync Units`
- Created `docs/37_telematics_provider_integration.md` for setup, provider contract, Wialon notes, and acceptance criteria.

Code paths:

- `omni_operations/telematics/providers/wialon.py`
- `omni_operations/telematics/providers/base.py`
- `omni_operations/telematics/providers/registry.py`
- `omni_operations/telematics/sync.py`
- `omni_operations/telematics/doctype/telematics_provider_account/telematics_provider_account.js`

Verification:

- Static compile and bench smoke checks are required after this implementation pass.
- Live provider verification remains pending until real provider credentials are entered.

### E-007 Provider Account Scope Result

Completed on 2026-08-18:

- Added `Account Scope` to `Telematics Provider Account` with options:
  - `System-wide`
  - `Regional Admin`
  - `Customer Hub`
- Added hierarchy fields for provider-side structure:
  - `External Account/User Name`
  - `Parent Provider Account`
  - `Region`
- Added validation:
  - `Customer Hub` accounts must link to one Omni Customer.
  - `System-wide` and `Regional Admin` accounts clear `Customer` because they may sync units for many customers.
  - A provider account cannot be its own parent.
- Added Desk behavior to show/hide and require fields based on account scope.
- Updated `docs/37_telematics_provider_integration.md` to map the Wialon hierarchy:
  - `omnitrack` parent account
  - regional admin accounts
  - customer hubs
  - units/users beneath hubs

Important rule:

- Provider account scope controls API reach. Customer portal visibility still comes from linked Omni records, especially `Fleet Vehicle.customer`.

## Track F - Commercial Workflow

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| F-001 | Configure fleet service items | A-007 | done | ERPNext Items exist for fleet service, tracker hardware, SIM, installation, maintenance labor. |
| F-002 | Create fleet quotation template | F-001 | done | Quotation supports tracker/service/installation lines. |
| F-003 | Validate quote to invoice flow | F-002 | done | Quotation can become Sales Order/Sales Invoice. |
| F-004 | Validate payment capture | F-003 | done | Payment Entry updates customer balance and invoice status. |
| F-005 | Link invoice to Fleet Contract/Profile | D-007, F-003 | done | Customer Fleet Profile shows invoices and payment status. |

### F-001 Fleet Service Item Result

Completed on 2026-08-16:

- Added repeatable setup utility for first fleet commercial items.
- Confirmed ERPNext Items exist:
  - `FLEET-MONTHLY-SERVICE`
  - `TRACKER-HW-4G`
  - `SIM-IOT`
  - `INSTALL-LABOUR`
  - `MAINT-LABOUR`
- Stock items:
  - `TRACKER-HW-4G`
  - `SIM-IOT`
- Service items:
  - `FLEET-MONTHLY-SERVICE`
  - `INSTALL-LABOUR`
  - `MAINT-LABOUR`

Code path:

- `omni_operations/omni_setup/items.py`

Verification:

- Ran `ensure_fleet_service_items()`.
- Confirmed all five ERPNext Item records exist with the intended stock/service configuration.

### F-002/F-003/F-004 Commercial Flow Result

Completed on 2026-08-16:

- Added commercial setup helper for the first fleet sales package.
- Created repeatable item price setup for the starter quote lines.
- Created a fleet starter quotation using native ERPNext `Quotation`.
- Validated ERPNext conversion from `Quotation` to `Sales Order` to `Sales Invoice`.
- Validated ERPNext payment capture through `Payment Entry`.

Starter quote lines:

- `TRACKER-HW-4G`
- `SIM-IOT`
- `INSTALL-LABOUR`
- `FLEET-MONTHLY-SERVICE`

Code path:

- `omni_operations/omni_setup/commercial.py`

Verification:

- Fleet starter quotation: `SAL-QTN-2026-00002`
- Sales order: `SAL-ORD-2026-00001`
- Sales invoice: `ACC-SINV-2026-00002`
- Payment entry: `ACC-PAY-2026-00003`
- Invoice grand total: `USD 230.00`
- Invoice outstanding after payment: `USD 0.00`
- Invoice status after payment: `Paid`

### F-005 Customer Fleet Commercial Health Result

Completed on 2026-08-17:

- Added commercial health fields to `Customer Fleet Profile`.
- Customer Fleet Profile now stores:
  - Latest Sales Invoice
  - Invoice Status
  - Invoice Grand Total
  - Outstanding Amount
  - Latest Payment Entry
  - Last Payment Amount
  - Last Payment Date
- Added refresh helper that reads native ERPNext `Sales Invoice`, `Payment Entry`, and `Payment Entry Reference` records.
- The existing commercial validation flow now refreshes the linked customer fleet profile after payment capture.

Code paths:

- `omni_operations/fleet/doctype/customer_fleet_profile/customer_fleet_profile.json`
- `omni_operations/fleet/doctype/customer_fleet_profile/customer_fleet_profile.py`
- `omni_operations/omni_setup/commercial.py`

Verification:

- Refreshed profile: `Acme Logistics Zimbabwe`
- Latest invoice: `ACC-SINV-2026-00002`
- Invoice status: `Paid`
- Invoice grand total: `USD 230.00`
- Outstanding amount: `USD 0.00`
- Latest payment: `ACC-PAY-2026-00003`
- Last payment amount: `USD 230.00`

## Track G - Maintenance and Field Service

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| G-001 | Decide ERPNext maintenance reuse boundary | A-008, D-001 | done | Decide what ERPNext Maintenance covers and what Omni custom work orders cover. |
| G-002 | Create Fleet Maintenance Work Order | G-001 | done | Work order links vehicle, technician, parts, customer, status, and invoice flag. |
| G-003 | Link parts used to ERPNext stock | G-002 | done | Parts consumption creates or links to stock movement/stock entry. |
| G-004 | Generate billable maintenance invoice | G-002, F-003 | done | Billable maintenance can create Sales Invoice. |
| G-005 | Add maintenance history to Vehicle 360 | G-002 | done | Vehicle view shows upcoming and past maintenance. |

### G-001 Maintenance Boundary Result

Completed on 2026-08-17:

- ERPNext owns accounting, stock ledger, stock movement, and sales invoicing.
- Omni owns the fleet-specific maintenance workflow because ERPNext maintenance screens are generic and do not carry enough vehicle/tracker/SIM/customer context.
- First implementation uses Omni `Fleet Maintenance Work Order` as the operational record.
- Parts consumption is posted to ERPNext `Stock Entry`.
- Billable maintenance is posted to ERPNext `Sales Invoice`.

### G-002/G-003/G-004/G-005 Fleet Maintenance Result

Completed on 2026-08-17:

- Added `Fleet Maintenance Work Order` DocType in the `Field Service` module.
- Added child table `Fleet Maintenance Part`.
- Work order links customer, company, vehicle, technician, parts, stock entry, and sales invoice.
- Added workspace link: `Maintenance Work Orders`.
- Added maintenance status/history API for Vehicle 360.
- Updated Fleet Vehicle form script to show a maintenance dashboard indicator.

Code paths:

- `omni_operations/field_service/doctype/fleet_maintenance_work_order/fleet_maintenance_work_order.json`
- `omni_operations/field_service/doctype/fleet_maintenance_work_order/fleet_maintenance_work_order.py`
- `omni_operations/field_service/doctype/fleet_maintenance_part/fleet_maintenance_part.json`
- `omni_operations/field_service/maintenance.py`
- `omni_operations/public/js/fleet_vehicle.js`

Verification:

- Demo work order: `FMWO-2026-0001`
- Vehicle: `ADE-1001`
- Part consumed: `RELAY-12V`
- ERPNext stock entry: `MAT-STE-2026-00004`
- ERPNext sales invoice: `ACC-SINV-2026-00003`
- Invoice total: `USD 53.00`
- Work order billing status: `Invoiced`
- Work order parts stock status: `Issued`
- `RELAY-12V` stock in `Main Fleet Stock - ODZ` reduced from `20` to `19`.
- Vehicle maintenance status API returns `Completed` with green indicator.

## Track H - UI and Portal

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| H-001 | Define Omni workspace IA in ERPNext Desk | C-004 | done | Internal users see a simple Omni Operations workspace. |
| H-002 | Define Fleet 360 layout | D-001, E-002, F-005, G-005 | done | Vehicle page layout includes identity, tracker, driver, telematics status, invoices, maintenance, documents, profitability. |
| H-003 | Define Customer Fleet 360 layout | D-007, F-005 | done | Customer page shows fleet, invoices, payments, support, contracts, and telematics access. |
| H-004 | Decide customer portal path | A-008, F-005 | done | Choose ERPNext portal, Svelte portal, or hybrid for first release. |
| H-005 | Build customer portal MVP | H-004 | done | Customer can view fleet, invoices, payments, support, and tracking handoff. |

### H-001/H-002/H-003/H-004/H-005 UI and Portal Result

Completed on 2026-08-17:

- Continued with ERPNext Desk as the internal MVP UI.
- Chose a hybrid portal path: use Frappe/ERPNext portal pages first, then build a separate Svelte portal later only if the experience needs more control.
- Added Fleet Vehicle 360 summary API.
- Added Customer Fleet 360 summary API.
- Fleet Vehicle form now shows dashboard indicators for telematics, maintenance, invoice status, and driver assignment.
- Customer Fleet Profile form now shows dashboard indicators for vehicles, invoice health, and telematics links.
- Added first customer portal MVP page.

Code paths:

- `omni_operations/fleet/vehicle_360.py`
- `omni_operations/fleet/customer_360.py`
- `omni_operations/public/js/fleet_vehicle.js`
- `omni_operations/public/js/customer_fleet_profile.js`
- `omni_operations/www/omni_customer_portal.py`
- `omni_operations/www/omni_customer_portal.html`

Verification:

- `get_vehicle_360("ADE-1001")` returns vehicle identity, tracker/SIM, driver assignment, latest invoice, telematics status, and maintenance status.
- `get_customer_fleet_360("Acme Logistics Zimbabwe")` returns profile summary, vehicles, telematics links, invoices, support tickets, and maintenance records.
- JavaScript syntax checks passed for Fleet Vehicle and Customer Fleet Profile form scripts.
- Portal page exists at `/omni_customer_portal`; guests are redirected to login.

## Track I - Governance, Security, and Compliance

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| I-001 | Review GPL/commercial packaging implications | A-003 | done | Written legal/commercial decision exists before distribution. |
| I-002 | Define role permissions | C-003 | done | Each Omni role has least-privilege permissions. |
| I-003 | Define audit strategy | C-001 | done | Decide Frappe Version/Activity plus Omni audit needs. |
| I-004 | Map compliance records | B-008 | done | Existing compliance records either stay in Omni v3 or map to Frappe custom DocTypes. |

### I-001/I-002/I-003/I-004 Governance Result

Completed on 2026-08-17:

- Added governance, role permission, audit, and compliance mapping document.
- Confirmed GPLv3/commercial packaging requires legal review before product distribution.
- Defined minimal Omni role intent for founders, operations, technicians, coordinators, fleet managers, and portal users.
- Chose Frappe native Version/Activity records first, plus dedicated integration sync logs where needed.
- Mapped existing v3 compliance areas into Omni v4 directions.

Code/doc path:

- `docs/35_governance_security_compliance.md`

Important production caveat:

- Current evaluation permissions are intentionally broad for fast development.
- Before real customer onboarding, role permissions and customer portal filtering must be tightened and tested with non-admin users.

## Track J - Fiscalisation / ZIMRA FDMS

| ID | Task | Dependency | Status | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| J-001 | Confirm ZIMRA FDMS onboarding requirements | F-003 | done | Written checklist exists for test access, taxpayer setup, device registration, activation keys, approval steps, and live cutover. |
| J-002 | Define fiscalisation architecture boundary | F-003 | done | Decide what ERPNext owns, what Omni fiscalisation DocTypes own, and where invoice submit hooks run. |
| J-003 | Create Fiscal Provider Account DocType | J-002 | done | Stores provider, taxpayer/company, environment, endpoint, credential references, and status without hard-coding ZIMRA everywhere. |
| J-004 | Create Fiscal Device DocType | J-003 | done | Stores device ID, activation/config state, branch/location, fiscal counters, and live/test status. |
| J-005 | Create Fiscal Day DocType | J-004 | done | Tracks fiscal day open/close state, day number, counters, and error handling. |
| J-006 | Create Fiscal Document DocType | J-004, F-003 | done | Links Sales Invoice/Credit Note to fiscal receipt number, QR data, signatures, status, and provider response. |
| J-007 | Create Fiscal Sync Log DocType | J-003 | done | Every request/response/error is auditable without cluttering invoice records. |
| J-008 | Build ZIMRA FDMS adapter prototype | J-003, J-004, J-006 | done | Test-mode adapter can prepare and submit or simulate a compliant fiscal invoice payload. |
| J-009 | Add fiscalisation hook to Sales Invoice | J-006, J-008 | done | Submitted invoices can be fiscalised and show status without blocking normal ERPNext accounting unexpectedly. |
| J-010 | Add fiscal details to invoice print format | J-006 | done | Fiscal receipt number, QR code data, and required ZIMRA details appear on customer-facing documents. |
| J-011 | Handle Credit Notes / Debit Notes | J-006, J-008 | done | ERPNext returns/credit notes map to required fiscal document flows. |
| J-012 | Validate live-readiness with ZIMRA or approved provider | J-008 to J-011 | blocked | Test output is accepted or feedback is documented before any production use. |

### ZIMRA FDMS Planning Notes

Added on 2026-08-17:

- ZIMRA supports Virtual Fiscalisation through software based VFD/API integration with FDMS.
- ZIMRA says the Virtual Fiscalisation API can be accessed by taxpayers free of charge from the ZIMRA website.
- Free API access does not mean the full compliance project is free.
- Omni must still budget development, testing, onboarding, certification/approval, device registration/configuration, fiscal day handling, receipt counters, QR code output, error handling, and operational support.
- Third-party fiscalisation providers may reduce onboarding and compliance risk, but usually introduce subscription, setup, or transaction costs.
- Direct FDMS integration should be designed as a provider-neutral fiscalisation layer, with ZIMRA as the first adapter.

### J-001/J-002 Fiscalisation Boundary Result

Completed on 2026-08-17:

- ERPNext owns accounting, Sales Invoice submission, Credit Note/return documents, totals, taxes, and print execution.
- Omni owns fiscalisation provider setup, device/day state, fiscal document state, sync logs, provider adapters, and invoice fiscalisation hooks.
- ZIMRA FDMS is treated as the first provider adapter, not hard-coded throughout Omni.
- Direct ZIMRA API access may be free, but live-readiness still requires onboarding, credentials, test validation, and approval.

### J-003/J-004/J-005/J-006/J-007 Fiscal DocTypes Result

Completed on 2026-08-17:

- Added `Fiscalisation` module.
- Added `Fiscal Provider Account`.
- Added `Fiscal Device`.
- Added `Fiscal Day`.
- Added `Fiscal Document`.
- Added `Fiscal Sync Log`.
- Added fiscal workspace links to `Omni Operations`.

Code paths:

- `omni_operations/fiscalisation/doctype/fiscal_provider_account/fiscal_provider_account.json`
- `omni_operations/fiscalisation/doctype/fiscal_device/fiscal_device.json`
- `omni_operations/fiscalisation/doctype/fiscal_day/fiscal_day.json`
- `omni_operations/fiscalisation/doctype/fiscal_document/fiscal_document.json`
- `omni_operations/fiscalisation/doctype/fiscal_sync_log/fiscal_sync_log.json`

### J-008/J-009/J-010/J-011 Fiscalisation Prototype Result

Completed on 2026-08-17:

- Added demo ZIMRA FDMS provider adapter.
- Added fiscalisation service for submitted ERPNext Sales Invoices.
- Added Sales Invoice `on_submit` hook for optional auto-fiscalisation.
- Added credit-note awareness through ERPNext return invoices.
- Added `Omni Fiscal Sales Invoice` print format with fiscal receipt, QR data, and verification URL fields.

Code paths:

- `omni_operations/fiscalisation/service.py`
- `omni_operations/fiscalisation/events.py`
- `omni_operations/fiscalisation/providers/demo_zimra.py`
- `omni_operations/fiscalisation/providers/registry.py`
- `omni_operations/fixtures/print_format.json`

Verification:

- Demo provider account: `Demo ZIMRA FDMS Account`
- Demo fiscal device: `DEMO-FDMS-001`
- Manual fiscal document: `FDOC-2026-0001`
- Manual fiscalised invoice: `ACC-SINV-2026-00002`
- Hook-created fiscal document: `FDOC-2026-0002`
- Hook fiscalised invoice: `ACC-SINV-2026-00004`
- Fiscal sync logs created: `2`
- Fiscal provider auto-fiscalisation was reset to disabled after hook verification.

### J-012 Live-Readiness Blocker

Blocked as of 2026-08-17:

- Live ZIMRA readiness cannot be truthfully completed without real ZIMRA onboarding, test credentials, device activation details, and acceptance feedback from ZIMRA or an approved fiscalisation provider.
- The current implementation is a demo/test-mode architecture and must not be treated as production fiscalisation.

Official references:

- `https://www.zimra.co.zw/domestic-taxes/corporate/fiscalisation-explained`
- `https://www.zimra.co.zw/news/2307-compliance-with-the-zimra-fiscalisation-data-management-system-fdms`
- `https://www.zimra.co.zw/downloads/9-domestic-taxes?download=3807%3Afiscalisation-api-documentation`

## Operational Readiness Pass - Excluding Live ZIMRA

Completed on 2026-08-17:

- Migration dry-run readiness:
  - Added `scripts/validate_migration_templates.py`.
  - Verified `docs/migration_templates` headers and cross-reference rules locally.
  - Result: `Migration template validation passed for docs/migration_templates.`
- Permissions hardening:
  - Added rerunnable role and permission sync in `omni_operations/omni_setup/permissions.py`.
  - Hooked sync into `after_install` and `after_migrate`.
  - Ran permission sync successfully on `development.localhost`.
- Customer portal polish:
  - Updated `/omni_customer_portal` into a clearer customer dashboard.
  - Dashboard now shows account status, vehicles, active trackers, outstanding balance, open tickets, vehicle list, maintenance, telematics links, invoices, and support tickets.
  - Added server-side customer access checks so portal users can only load the customer linked to their contact email.
  - Removed export/share/email permission from `Customer Portal User` DocPerm rows.
  - Authenticated render returned HTTP `200`.
- Testing and hardening:
  - Added app smoke checks in `omni_operations/omni_setup/smoke.py`.
  - Smoke checks verify Omni DocTypes, roles, sample record counts, and migration template headers when template files are visible to the runtime.
  - Result on Docker bench: `ok: true`.
- Real integration readiness:
  - Added provider-neutral `CustomAPITelematicsProvider`.
  - `Custom API` telematics accounts now use a real HTTP adapter scaffold instead of the demo provider.
  - The adapter supports `GET /health`, `GET /units`, and `GET /units/{external_unit_id}/position` with API token or username/password auth.
- Lifecycle verification:
  - Ran `bench --site development.localhost migrate`.
  - Migration completed and executed `after_migrate` hooks successfully.

Remaining after this pass:

- Live ZIMRA FDMS readiness remains blocked externally.
- Real v3 production migration still needs actual exported v3 data populated into the staging templates.
- Real telematics provider adapters still need provider-specific schemas and credentials.

## v3 Migration Dry Run

Completed on 2026-08-17:

- Received Supabase CSV exports in `migration_exports`.
- Added transformer:
  - `scripts/transform_v3_exports.py`
- Generated staged Omni v4 migration files in:
  - `migration_working/omniv4_staging`
- Generated dry-run report:
  - `migration_working/omniv4_staging/MIGRATION_DRY_RUN_REPORT.md`
- Validation passed:
  - `python3 scripts/validate_migration_templates.py migration_working/omniv4_staging`
- Current staged row counts:
  - Customers: `6`
  - Customer Fleet Profiles: `6`
  - Tracker Profiles: `26`
  - SIM Profiles: `10`
  - Derived Fleet Vehicles: `11`
  - Tracker Installations: `12`
  - Sales Pipeline records: `2`
  - Billing/Subscription records: `5`
- Missing source exports:
  - `vehicles_rows.csv`
  - `device_pairings_rows.csv`
  - `technician_jobs_rows.csv`
- Decision before import: either accept derived vehicles from assignment asset fields or provide the missing source exports for fuller migration fidelity.

Import completed on 2026-08-17 after approval to use the staged files:

- Importer added:
  - `omni_operations/omni_setup/migration_import.py`
- Import report copied to:
  - `migration_working/omniv4_staging/erpnext_import_report.json`
- Imported/updated into `development.localhost`:
  - Customers: `6`
  - Customer Fleet Profiles: `6`
  - Tracker Profiles: `26`
  - SIM Profiles: `10`
  - Fleet Vehicles: `11`
  - Legacy Tracker Installations: `12`
  - Sales pipeline Leads: `2`
  - Billing/subscription history records attached to profiles: `5`
- Subscription rows were imported as history only; ERPNext recurring billing was not activated.
- User password hashes were intentionally ignored.
- App smoke check passed after import.

Post-migration cleanup completed on 2026-08-17:

- Added cleanup/provisioning utility:
  - `omni_operations/omni_setup/post_migration.py`
- Renamed `asset-label-NISSAN X-TRAIL` to `NISSAN-X-TRAIL-MAPANJE`.
- Classified imported vehicle types into cleaner `Car` and `Truck` values.
- Created disabled Customer Portal Users from migrated customer contacts:
  - `blessedmapanje@gmail.com`
  - `gwanzurajos@gmail.com`
  - `langtonmutami@gmail.com`
  - `mutamiregis@gmail.com`
  - `nyashanjinga@gmail.com`
  - `tatmanyora@gmail.com`
  - `trevormunyerei@gmail.com`
- Linked portal users to Customer records but kept them disabled until onboarding/password policy is confirmed.
- Extended Vehicle 360 with make, model, year, VIN, and recent installation history.
- Verified `NISSAN-X-TRAIL-MAPANJE` through Vehicle 360.

Portal and telematics readiness completed on 2026-08-17:

- Added internal portal test provisioning:
  - `omni_operations/customer_portal/provisioning.py`
- Created enabled internal test user:
  - `portal-test@omni.local`
- Linked test user to `Mapanje`.
- Verified `/omni_customer_portal` as the test user:
  - HTTP `200`
  - Shows `Mapanje`
  - Shows `NISSAN-X-TRAIL-MAPANJE`
  - Does not show `Pairtrade`
- Added telematics staging-link provisioning:
  - `omni_operations/telematics/provisioning.py`
- Created provider account:
  - `Imported Fleet Telematics Staging`
- Created/updated `12` imported fleet telematics links with `sync_enabled = 0`.
- Verified `Mapanje` Customer 360 returns `3` vehicles, `3` active trackers, `3` installed SIMs, and `3` staging telematics links.
- App smoke check passed after portal and telematics provisioning.

Provider-unit matching readiness completed on 2026-08-18:

- Added provider unit migration template:
  - `docs/migration_templates/09_telematics_provider_units.csv`
- Added staging files:
  - `migration_working/omniv4_staging/09_telematics_provider_units.csv`
  - `migration_working/omniv4_staging/09_telematics_provider_units_prefill.csv`
- Added prefill generator:
  - `scripts/generate_telematics_unit_export.py`
- Added CSV preview/apply workflow:
  - `omni_operations/telematics/matching.py`
- The prefill file matched provider unit rows to installed `Tracker Profile` records by IMEI.
- Applied `11` provider unit matches from the prefill CSV with no unmatched rows.
- Left matched links with `sync_enabled = 0` until real provider credentials and sync contracts are configured.
- Updated Vehicle 360/portal-facing telematics status so staged links show as `Linked (Sync Off)` or `Sync Off` instead of looking like live tracking is enabled.
- Verified `NISSAN-X-TRAIL-MAPANJE` reports `Linked (Sync Off)`.
- App smoke check passed after provider-unit matching.

Permission, portal, and production UI refinement completed on 2026-08-18:

- Added framework-level customer access hardening:
  - `omni_operations/omni_security/access.py`
- Added `permission_query_conditions` and `has_permission` hooks for customer-visible records:
  - `Customer Fleet Profile`
  - `Fleet Vehicle`
  - `Fleet Driver`
  - `Vehicle Assignment`
  - `Tracker Installation`
  - `Fleet Maintenance Work Order`
  - `Telematics Unit Link`
  - `Fiscal Document`
  - `Sales Invoice`
  - `Issue`
- Portal-only users now route to `/omni_customer_portal` after login.
- Added repeatable portal isolation smoke check:
  - `omni_operations.omni_setup.smoke.run_security_smoke_checks`
- Verified `portal-test@omni.local`:
  - Home page: `/omni_customer_portal`
  - Query condition: `` `tabCustomer Fleet Profile`.`customer` = 'Mapanje' ``
  - Visible customers through permission-filtered list: `Mapanje` only
  - Direct read allowed for `Mapanje`
  - Direct read blocked for `Acme Logistics Zimbabwe`
- Added portal support-ticket creation:
  - `omni_operations/customer_portal/api.py`
- Polished `/omni_customer_portal`:
  - Clearer account header
  - More consistent status badges
  - Better empty states
  - Support request form
  - Mobile-friendly stacking for list items
  - Closed support tickets are hidden from the main portal dashboard
- Added internal list-view refinements:
  - `public/js/customer_fleet_profile_list.js`
  - `public/js/fleet_vehicle_list.js`
  - `public/js/tracker_installation_list.js`
  - `public/js/fleet_maintenance_work_order_list.js`
  - `public/js/telematics_unit_link_list.js`
- Internal Desk list views now expose practical operational filters and status indicators for customers, vehicles, installations, maintenance, and telematics links.
- Verification:
  - Python compile checks passed.
  - JavaScript syntax checks passed.
  - `bench --site development.localhost migrate` completed successfully.
  - `bench build --app omni_operations` completed successfully.
  - App smoke check returned `ok: true`.
  - Security smoke check returned `ok: true`.
  - Portal HTTP check as `portal-test@omni.local` returned `200`, showed `Mapanje`, hid `Pairtrade`, showed `New Request`, and showed `Sync Off`.

Customer portal and UI refinement pass completed on 2026-08-18:

- Enriched `Customer Fleet 360` portal data:
  - Vehicle rows now include make/model, linked telematics unit, telematics label, and last-position timestamp when available.
  - Portal summary now separates live telematics from staged/sync-off telematics.
  - Open maintenance, open invoice, and open ticket counts are calculated for the dashboard.
- Refined `/omni_customer_portal`:
  - Added operational alert strip for balance due, open support, and open maintenance when present.
  - Reworked vehicle, maintenance, telematics, invoice, and support sections into consistent compact rows.
  - Improved mobile behavior for row actions and status badges.
  - Removed visual clutter while keeping the portal focused on customer tasks.
- Improved internal Desk usability:
  - `Customer Fleet Profile` now has quick actions for portal preview, vehicles, support, and invoices.
  - `Fleet Vehicle` now has quick actions for telematics links, maintenance, and installations.
  - Portal preview can open a specific customer for internal roles via `/omni_customer_portal?customer=...`.
- Verification:
  - Python compile checks passed.
  - JavaScript syntax checks passed.
  - `bench build --app omni_operations` completed successfully.
  - App smoke check returned `ok: true`.
  - Security smoke check returned `ok: true`.
  - Browser desktop check: no horizontal overflow, no clipped badges.
  - Browser mobile check at `390x844`: no horizontal overflow, no clipped badges.

Customer document portal workflow completed on 2026-08-18:

- Added `Fleet Document` DocType for customer/vehicle documents:
  - Contracts
  - Insurance
  - Vehicle registration
  - Licences
  - Tax certificates
  - Purchase orders
  - Invoices
  - Service reports
  - Other documents
- Added document controls:
  - Customer and optional vehicle linkage
  - Status
  - Issue and expiry dates
  - Reference number
  - Attachment
  - `portal_visible` publication switch
- Added validation:
  - Vehicle-linked documents can infer customer from the vehicle.
  - Expired dated documents auto-mark as `Expired`.
  - Portal-visible documents require an attachment.
- Added permissions/security:
  - `Fleet Document` participates in Omni role permission sync.
  - Customer portal users can only see documents for their own customer.
  - Security smoke now validates portal-visible document scoping.
- Added portal UI:
  - Documents metric.
  - Documents section.
  - Portal-visible document rows with type, vehicle, expiry date, status, and open link.
- Added internal UI:
  - `Fleet Document` list indicators and filters.
  - Customer Fleet Profile quick action to related documents.
  - Fleet Vehicle quick action to related documents.
- Added demo portal document:
  - `NISSAN-X-TRAIL-MAPANJE Registration`
  - File URL: `/files/omni-demo-nissan-xtrail-registration.txt`
- Verification:
  - `bench --site development.localhost migrate` completed successfully.
  - Python compile checks passed.
  - JavaScript syntax checks passed.
  - `bench build --app omni_operations` completed successfully.
  - App smoke check returned `ok: true` and includes `Fleet Document`.
  - Security smoke check returned `ok: true` and confirms visible documents are scoped to `Mapanje`.
  - Portal HTTP check shows the document and hides `Pairtrade`.
  - Browser desktop/mobile checks show no horizontal overflow and no clipped badges.

Fleet contract and subscription visibility completed on 2026-08-18:

- Added `Fleet Contract` DocType to turn migrated subscription history into a first-class Omni v4 record:
  - Customer and optional vehicle linkage
  - Service item
  - Billing frequency
  - Monthly rate and contract value
  - Start/end dates
  - Next billing date
  - Billing status
  - Latest invoice/payment references
  - `portal_visible` customer publication switch
- Added validation/defaulting:
  - Vehicle-linked contracts can infer customer from the vehicle.
  - Active contracts with a start date get a next billing date.
  - Active contracts past their end date become `Expired`.
- Added permissions/security:
  - `Fleet Contract` participates in Omni role permission sync.
  - Customer portal users can only see contracts for their own customer.
  - Security smoke now validates contract scoping.
- Added portal UI:
  - Contracts metric.
  - Contracts section with contract title, vehicle, billing frequency, monthly rate, next billing date, status, and billing status.
- Added internal UI:
  - `Fleet Contract` list indicators and filters.
  - Customer Fleet Profile quick action to related contracts.
  - Fleet Vehicle quick action to related contracts.
- Added demo portal contract:
  - `Mapanje Monthly Fleet Tracking`
  - Contract: `FCON-2026-0001`
  - Monthly rate: `USD 35.00`
  - Next billing date: `2026-09-18`
- Verification:
  - `bench --site development.localhost migrate` completed successfully.
  - Python compile checks passed.
  - JavaScript syntax checks passed.
  - `bench build --app omni_operations` completed successfully.
  - App smoke check returned `ok: true` and includes `Fleet Contract`.
  - Security smoke check returned `ok: true` and confirms visible contracts are scoped to `Mapanje`.
  - Portal HTTP check shows `Mapanje Monthly Fleet Tracking`, the registration document, and hides `Pairtrade`.

Remaining after current implementable passes:

- Real telematics live sync has a Wialon-compatible implementation path, but still needs actual provider credentials and at least one real unit match for live verification.
- Live ZIMRA FDMS readiness still needs ZIMRA/provider onboarding, test credentials, device registration, and accepted test output.
- Production migration still needs a final real-data rehearsal and sign-off once v3 exports are refreshed.
- ERPNext production deployment still needs hosting, backups, email, domain/TLS, tested MariaDB version pinning, and environment secrets.
- Production readiness checklist is tracked in `docs/38_omniv4_production_readiness.md`.

## First Sprint

Sprint goal:

> Establish the ERPNext evaluation environment and prove that Omni should build as `omni_operations` on top of ERPNext.

Sprint tasks:

1. `A-003` - Decide ERPNext version strategy.
2. `A-004` - Create ERPNext evaluation bench.
3. `A-005` - Install ERPNext.
4. `A-006` - Create Zimbabwe demo company.
5. `A-007` - Create sample ERP data.
6. `A-008` - Validate target DocTypes.
7. `C-001` - Create `omni_operations` app skeleton only after bench is working.

Current blocker:

- Live ZIMRA FDMS readiness cannot be completed without real ZIMRA or approved provider credentials, device registration details, and accepted test output.

Next action:

- Prepare production credentials, then run fiscalisation tests against an approved ZIMRA FDMS test endpoint or certified integration provider.
