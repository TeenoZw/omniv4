# Omni v3 to Omni v4 Migration Map

Date: 2026-08-17

This document closes the Track B planning gap by mapping the existing Omni v3 data model to the ERPNext-backed Omni v4 model.

Omni v4 keeps ERPNext as the business backbone and uses `omni_operations` for fleet, tracker, SIM, telematics, installation, maintenance, customer fleet, and fiscalisation depth.

## Migration Principles

- Preserve every v3 record with its legacy identifier in an import column named `legacy_*`.
- Import master data before transactions or operational history.
- Create shared ERPNext records once, then link Omni records to them.
- Keep customers, vehicles, trackers, SIMs, users, warehouses, items, invoices, and fiscal documents in one shared model.
- Treat uncertain v3 fields as notes during first import; promote them to formal fields only when they drive workflow, reporting, or compliance.
- Do not import deleted/recycled v3 records as active records; stage them separately for audit review.

## Recommended Import Order

1. Customers and contacts from `hubs`
2. Customer Fleet Profiles from `hubs`
3. Items and warehouses for tracker/SIM/service stock
4. Tracker Profiles from `hardware_inventory`
5. SIM Profiles from `sim_inventory`
6. Fleet Vehicles from `vehicles`
7. Tracker Installations from active `hardware_assignments`, `sim_assignments`, and approved `device_pairings`
8. Sales pipeline records from `enquiries`
9. Billing and subscriptions from `subscriptions`
10. Technician work from `technician_jobs`

## B-001 Hub Mapping

Source table: `hubs`

Primary targets:

- ERPNext `Customer`
- ERPNext `Contact`
- ERPNext `Address`
- Omni `Customer Fleet Profile`

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `id` | `legacy_hub_id` | Store in import template and, later, a custom legacy reference field if needed. |
| `name` | Customer `customer_name` | Main account name. |
| `code` | Customer `customer_code` or legacy field | Must remain searchable because v3 UI used hub context heavily. |
| `hub_type` | Customer `customer_group` | Map `business`/fleet customers to commercial groups. |
| `status` | Customer/Profile status | Active hubs become enabled customers; inactive/deleted hubs need review. |
| `country`, `city`, `address_line`, `location` | Address fields | Prefer structured address fields; keep raw `location` in notes if ambiguous. |
| `currency` | Customer default currency | Also verify company currency. |
| `timezone` | Customer Fleet Profile `timezone` or notes | Operational context. |
| `go_live_date` | Customer Fleet Profile `go_live_date` | Useful for onboarding history. |
| `primary_contact_*` | Contact | Primary operational contact. |
| `billing_contact_*` | Contact | Create separate contact when different from primary. |
| `device_count`, `vehicle_count` | Customer Fleet Profile summary | Counts should be recalculated after vehicle/tracker import. |
| `latitude`, `longitude` | Address/geolocation notes | Use when a formal geolocation field exists. |
| `subscription_tier`, `billing_cycle`, `payment_method` | Fleet Contract or Subscription staging | Do not hide billing fields inside Customer only. |
| `notes`, `description` | Customer/Profile notes | Preserve original free text. |

## B-002 Enquiry Mapping

Source table: `enquiries`

Primary targets:

- ERPNext `Lead`
- ERPNext `Opportunity`
- ERPNext `Quotation`
- ERPNext `Customer`, when `status = onboarded`

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `id` | `legacy_enquiry_id` | Preserve for audit and support lookups. |
| `status` | Lead/Opportunity stage | `new` -> Lead; `quoted`/`awaiting_payment` -> Opportunity/Quotation; `onboarded` -> Customer; `closed_lost` -> lost Opportunity. |
| `customer_type` | Lead type / Customer group | Individual vs business. |
| `full_name`, `email`, `phone` | Lead and Contact | Minimum identity fields. |
| `company_name` | Lead organization / Customer | If missing, use full name as individual customer name. |
| `fleet_size` | Opportunity notes / custom field | Convert to numeric only when clean. |
| `operating_area` | Territory / notes | Useful for fleet deployment planning. |
| `preferred_contact_method` | Lead notes | Use for follow-up workflow. |
| `expected_go_live_date` | Opportunity expected closing / Profile go-live | Operational planning. |
| `tracking_use_case` | Opportunity notes | Helps sales qualification. |
| `hardware_choices`, `add_ons` | Quotation Items / notes | Convert known SKUs to Items; keep unmatched values in notes. |
| `quoted_monthly`, `quoted_hardware_total` | Quotation totals / recurring contract staging | Validate pricing before posting accounting documents. |
| `quote_sent_at`, `responded_at`, `closed_at` | Lead/Opportunity timeline notes | Preserve lifecycle history. |
| `terms_accepted`, `privacy_accepted` | Compliance notes | Do not create portal access unless both are true or manually approved. |
| `admin_notes`, `message` | Lead/Opportunity notes | Preserve raw text. |

## B-003 Hardware Inventory Mapping

Source tables: `hardware_inventory`, `hardware_assignments`, `device_pairings`

Primary targets:

- ERPNext `Item`
- ERPNext `Serial No`
- Omni `Tracker Profile`
- Omni `Tracker Installation`
- Omni `Telematics Unit Link`, where a provider unit already exists

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `hardware_inventory.id` | `legacy_hardware_id` | Preserve for assignment reconciliation. |
| `imei` | Tracker Profile `imei`; Serial No serial identifier | Unique tracker identity. |
| `serial_number` | Serial No / Tracker Profile `serial_no` | Use when distinct from IMEI. |
| `hardware_type`, `model`, `manufacturer` | Tracker Profile metadata and Item variant | Keep saleable SKU in Item, physical device in Tracker Profile. |
| `firmware_version` | Tracker Profile `firmware_version` | Current firmware only; historical firmware needs future log. |
| `purchase_date`, `purchase_cost` | Stock valuation or notes | Use ERPNext stock opening balance when importing real inventory. |
| `status` | Tracker Profile status | Map `in_stock`, `assigned`, `active`, `faulty`, `maintenance`, `retired`. |
| `assignments.vehicle_id` | Tracker Installation vehicle | Active assignment becomes installed/active installation. |
| `assignments.hub_id` | Tracker Installation customer via hub mapping | Customer must exist first. |
| `installed_at`, `installation_location`, lat/lng | Tracker Installation fields | Preserve installation proof. |
| `pairings.status` | Tracker Installation approval status / notes | Approved pairings can become completed installations. |
| `notes` | Tracker Profile or Installation notes | Preserve raw operational context. |

## B-004 SIM Inventory Mapping

Source tables: `sim_inventory`, `sim_assignments`

Primary targets:

- ERPNext `Item`
- ERPNext `Serial No` or `Batch`
- Omni `SIM Profile`
- Omni `Tracker Installation`, when assigned to a tracker/vehicle

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `sim_inventory.id` | `legacy_sim_id` | Preserve for assignment reconciliation. |
| `iccid` | SIM Profile `iccid`; Serial No | Unique SIM identity. |
| `msisdn` | SIM Profile `msisdn` | Phone number. |
| `carrier` | SIM Profile `carrier` | Default v3 carrier was Econet. |
| `apn` | SIM Profile `apn` or IMSI/APN note | v3 schema labels this as APN while API serializes it as IMSI in places; verify during import. |
| `roaming_enabled`, `roaming_regions` | SIM Profile roaming fields | Operational connectivity detail. |
| `status` | SIM Profile status | Map `in_stock`, `assigned`, `suspended`, `faulty`, `retired`. |
| `assignments.hardware_id` | SIM Profile current tracker / Tracker Installation SIM | Link through tracker import. |
| `assignments.vehicle_id`, `hub_id` | SIM Profile current vehicle/customer | Link through vehicle/customer import. |
| `assigned_at`, `unassigned_at`, `is_active` | Installation/assignment history notes | Active records drive current links. |

## B-005 Vehicle and Asset Mapping

Source table: `vehicles`

Primary targets:

- Omni `Fleet Vehicle`
- ERPNext `Asset`, only for assets owned by Omni or when formal asset accounting is required
- Omni `Customer Fleet Profile`

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `id` | `legacy_vehicle_id` | Preserve for tracker/SIM/job reconciliation. |
| `hub_id` | Fleet Vehicle `customer` via hub mapping | Hub/customer import must run first. |
| `asset_type`, `asset_type_other` | Fleet Vehicle `vehicle_type` / notes | v3 vehicles may represent non-vehicle tracked assets. |
| `asset_name` | Fleet Vehicle title/name | Use registration or asset name for human-readable identity. |
| `license_plate` | Fleet Vehicle `registration_number` | Unique when present. |
| `vin` | Fleet Vehicle `vin` | Unique when present. |
| `make`, `model`, `year`, `color`, `fuel_type` | Fleet Vehicle details | Keep operational metadata. |
| `engine_capacity`, `co2_emissions` | Fleet Vehicle notes or future emissions fields | Do not lose environmental/compliance detail. |
| `imei` | Link to Tracker Profile by IMEI | Legacy shortcut; canonical tracker link should come from assignments. |
| `source_job_id` | Installation/Maintenance reference | Links back to technician job import. |
| `photo_url` | Attachment migration backlog | Import attachments after core data. |
| `status` | Fleet Vehicle status | Map `active`, `inactive`, `maintenance`, `retired`. |
| `notes` | Fleet Vehicle notes | Preserve raw context. |

## B-006 Technician Job Mapping

Source table: `technician_jobs`

Primary targets:

- Omni `Tracker Installation`, for installation/pairing work
- Omni `Fleet Maintenance Work Order`, for maintenance/repair work
- ERPNext `Issue`, when the job came from support

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `id` | `legacy_technician_job_id` | Preserve for audit trail. |
| `hub_id` | Customer via hub mapping | Customer must exist first. |
| `hardware_id` | Tracker Profile via hardware mapping | Optional but important for installation jobs. |
| `vehicle_id` | Fleet Vehicle via vehicle mapping | Optional for early scheduling. |
| `requested_by`, `assigned_technician_id` | User/technician fields | Map known users; otherwise retain as notes. |
| `status` | Installation or Work Order status | `completed` -> Completed, `cancelled` -> Cancelled, active states remain open. |
| `priority` | Work Order priority | Preserve urgency. |
| `scheduled_for`, `started_at`, `accepted_at`, `completed_at`, `cancelled_at`, `declined_at`, `installed_at` | Timeline fields/notes | Keep date history for service reporting. |
| `installation_location`, lat/lng | Tracker Installation location | Preserve proof of work location. |
| `asset_label`, `asset_registration` | Vehicle notes / registration hint | Useful when no vehicle record exists yet. |
| `notes`, `completion_notes`, `decline_reason` | Notes | Preserve technician context. |
| `assignment_reference` | External/reference field | Useful for support lookup. |

## B-007 Billing and Subscription Mapping

Source table: `subscriptions`; billing context also exists on `hubs`.

Primary targets:

- ERPNext `Sales Invoice`
- ERPNext `Payment Entry`
- ERPNext `Subscription`, if recurring billing is enabled
- Omni `Fleet Contract`, when the contract DocType is added

| v3 field | v4 target | Notes |
| --- | --- | --- |
| `id` | `legacy_subscription_id` | Preserve for reconciliation. |
| `hub_id` | Customer via hub mapping | Required. |
| `user_id` | Contact/User reference | Optional for customer portal access. |
| `tier` | Item/price plan or Fleet Contract plan | Use approved Omni service items. |
| `start_date`, `end_date` | Subscription/Fleet Contract dates | Defines billing period. |
| `is_active`, `auto_renew` | Subscription/Fleet Contract status | Active recurring records should be reviewed before enabling auto billing. |
| Hub `billing_cycle` | Billing frequency | Monthly/annual/etc. |
| Hub `payment_method` | Payment terms or notes | Do not assume payment gateway integration. |
| Hub `subscription_tier` | Plan | Validate against Item master. |

## B-008 Import Templates

Templates live in `docs/migration_templates/`:

- `01_customers_from_hubs.csv`
- `02_customer_fleet_profiles_from_hubs.csv`
- `03_tracker_profiles_from_hardware.csv`
- `04_sim_profiles_from_sim_inventory.csv`
- `05_fleet_vehicles_from_vehicles.csv`
- `06_tracker_installations_from_assignments.csv`
- `07_sales_pipeline_from_enquiries.csv`
- `08_billing_subscriptions.csv`

These are staging templates. Before a production import, export v3 data into these columns, validate required references, then transform into Frappe/ERPNext Data Import format.

## Cutover Checks

- All rows have a populated `legacy_*` identifier.
- No active tracker has more than one active vehicle assignment.
- No active SIM has more than one active tracker assignment.
- Every active vehicle resolves to exactly one Customer.
- Every active subscription resolves to an approved Item/plan.
- Every submitted invoice that requires fiscalisation is blocked from production use until ZIMRA FDMS credentials, test submission approval, QR/verification payload requirements, and live cutover are confirmed.
- Deleted/recycled v3 hubs are reviewed manually before import.
