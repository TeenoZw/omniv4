# 37 - Telematics Provider Integration

## Purpose

Omni v4 should treat Wialon, Traccar, Navixy, Teltonika, Ruptela, and future platforms as interchangeable telematics providers.

The shared Omni concepts are:

- `Telematics Provider Account` - credentials, API endpoint, status, and sync health.
- `Telematics Unit Link` - maps an external telematics unit to an Omni vehicle, tracker, SIM, installation, and customer.
- `Telematics Sync Log` - audit trail for account checks, unit syncs, latest position syncs, diagnostics, and manual imports.

Provider-specific code must stay inside `omni_operations/telematics/providers/`. The rest of Omni should depend on the shared provider interface, not a vendor name.

## Account Scope

Wialon service hierarchy can be broader than a single customer. Omni supports three provider account scopes:

- `System-wide` - top-level provider/API account, such as an `omnitrack` parent user that can read units across regions and hubs.
- `Regional Admin` - provider/API account for a region, such as Harare Admin or Midlands Admin, that can read multiple customer hubs below it.
- `Customer Hub` - provider/API account for one customer hub, such as H2O Hub, Mapanje Hub, Mutami Hub, or Pairtrade Hub.

Rules:

- `Customer Hub` accounts must link to one Omni `Customer`.
- `System-wide` and `Regional Admin` accounts should leave `Customer` blank because they can manage units belonging to many customers.
- Customer portal access must never depend on provider account scope. It must come from the linked `Fleet Vehicle.customer` and customer-scoped portal permissions.
- A single system-wide or regional provider account can sync units for many customer vehicles as long as each `Telematics Unit Link` maps the external unit to the correct Omni vehicle.
- In Omni, live Wialon customer ownership should use hub names as the Customer record, for example `H2O Hub`, `Mapanje Hub`, `Mutami Hub`, `Pairtrade Hub`, `Gwanzura Hub`, `Nenzou Hub`, and `Samarz Hub`.
- When a real registration number is missing, use a temporary registration in the format `WIALON-<external_unit_id>` and keep the previous label or source note in the vehicle notes.

## Current Provider Support

| Provider | Status | Notes |
| --- | --- | --- |
| Other | Demo fallback | Useful for staged imports and local smoke checks. |
| Custom API | Scaffolded | Generic API-token provider for future lightweight integrations. |
| Wialon | First real adapter | Uses token login, unit search, and latest position payloads. |
| Traccar | Planned | Add when credentials/API target are available. |
| Navixy | Planned | Add when credentials/API target are available. |
| Teltonika Telematics | Planned | Add when credentials/API target are available. |
| Ruptela | Planned | Add when credentials/API target are available. |

## Wialon Setup

Create a `Telematics Provider Account`:

- Provider: `Wialon`
- Account Scope: choose `System-wide`, `Regional Admin`, or `Customer Hub` based on the Wialon user/token you are using.
- Auth Type: `API Token`
- API Base URL: leave blank for Wialon Hosting default `https://hst-api.wialon.com`, or enter a regional/private host if your account uses one.
- Access Token: paste the Wialon token.
- Status: start as `Testing`; move to `Active` after connection and sync checks pass.
- Sync Enabled: leave unchecked while staging; check it only when the account is ready for automatic sync.

Then:

1. Click `Check Connection`.
2. Confirm a successful `Telematics Sync Log` with Sync Type `Account Check`.
3. Create or import `Telematics Unit Link` records for units that should map to Omni vehicles.
4. Click `Sync Units`.
5. Confirm matched unit links now show external name/device metadata and latest position data when `Sync Enabled` is on.

## Automatic Sync

Omni registers an hourly Frappe scheduler task:

```text
omni_operations.telematics.scheduled.sync_enabled_provider_accounts
```

The task syncs only `Telematics Provider Account` records where:

- `Status` is `Active`
- `Sync Enabled` is checked

Each run calls the same provider-neutral unit sync service used by the manual `Sync Units` button, so it still creates `Telematics Sync Log` records and updates matched `Telematics Unit Link` rows. Latest position fields update only on unit links where `Sync Enabled` is checked.

Manual run command:

```bash
cd /workspace/development/frappe-bench
bench --site development.localhost execute omni_operations.telematics.scheduled.sync_enabled_provider_accounts
```

Local scheduler checks:

```bash
bench --site development.localhost scheduler status
bench --site development.localhost doctor
```

If the scheduler is disabled in a local bench, enable it with:

```bash
bench --site development.localhost enable-scheduler
```

## Wialon Technical Basis

Wialon requests use the Remote API endpoint `/wialon/ajax.html` with `svc`, `params`, and a session id (`sid`) after login.

The first adapter uses:

- `token/login` to exchange an access token for a session id.
- `core/search_items` to list `avl_unit` records.
- unit data flags `1025` to request unit name plus latest position data.
- `core/search_item` for a single unit's latest position.
- `core/logout` after the request window.

References:

- [Wialon API user guide](https://help.wialon.com/en/api/user-guide)
- [Wialon token/login reference](https://help.wialon.com/en/api/user-guide/api-reference/token/login)
- [Wialon core/search_items reference](https://help.wialon.com/en/api/user-guide/api-reference/core/search_items)
- [Wialon FAQ latest coordinates example](https://help.wialon.com/en/api/expert-articles/faq/frequently-asked-questions)

## Provider Adapter Contract

Each provider adapter must implement:

- `check_connection()` - validates credentials/API reachability.
- `list_units()` - returns `ProviderUnit` rows with external id, name, device id, IMEI, group, timezone, optional position, and raw payload.
- `get_latest_position(external_unit_id)` - returns normalized latest position data.

Normalized position keys:

- `latitude`
- `longitude`
- `speed`
- `ignition`
- `odometer`
- `timestamp`
- `raw`

## Acceptance Criteria

- Real provider credentials are stored only in `Telematics Provider Account` password fields.
- Unit sync updates metadata for matched `Telematics Unit Link` records.
- Latest position fields update only when the unit link has `Sync Enabled` checked.
- Every account check or sync creates a `Telematics Sync Log`.
- Automatic sync runs only for active provider accounts where `Sync Enabled` is checked.
- Provider-specific errors are stored in sync health fields and logs.
- Adding a new provider should not require changing fleet, portal, accounting, or maintenance records.
