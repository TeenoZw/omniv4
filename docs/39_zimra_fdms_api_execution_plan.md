# 39 - ZIMRA FDMS API Execution Plan

## Source Reviewed

- ZIMRA Fiscal Device Gateway API Specification v7.2
- Public document URL: `https://www.zimra.co.zw/downloads/9-domestic-taxes?download=3807:fiscalisation-api-documentation`

## Confirmed API Shape

The ZIMRA Fiscal Device Gateway API is a REST JSON API. Every request must include:

- `DeviceModelName`
- `DeviceModelVersionNo`

The integration is not a simple API-token integration. ZIMRA uses mutual TLS after device registration. The public unauthenticated endpoints are:

- `verifyTaxpayerInformation`
- `registerDevice`
- `getServerCertificate`

After registration, most API methods require the FDMS-issued fiscal device certificate.

## Environments

| Environment | URL |
| --- | --- |
| Test | `https://fdmsapitest.zimra.co.zw` |
| Test Swagger | `https://fdmsapitest.zimra.co.zw/swagger/index.html` |
| Production | `https://fdmsapi.zimra.co.zw` |

## Required Credentials and Onboarding Inputs

Before live implementation can be tested, Omni needs:

- ZIMRA taxpayer TIN
- VAT number, if VAT registered
- Device ID
- Activation key
- Device serial number
- Device model name registered with ZIMRA
- Device model version number registered with ZIMRA
- Branch name and branch address
- Confirmation of device operating mode: `Online` or `Offline`
- Certificate signing key strategy
- FDMS-issued device certificate
- Certificate expiry policy and renewal process

## Device Lifecycle

1. Verify taxpayer information using device ID, activation key, and device serial number.
2. Generate private key and CSR.
3. Register the device with FDMS using `registerDevice`.
4. Store the issued X.509 certificate.
5. Call `getConfig` to pull taxpayer/device config, applicable taxes, certificate expiry, and QR URL.
6. Open a fiscal day.
7. Submit receipts/invoices/credit notes/debit notes.
8. Store FDMS operation IDs, receipt numbers, signatures, QR values, and errors.
9. Close fiscal day and store closure status/signature.
10. Renew certificate before expiry.

## Omni Data Model Alignment

The Fiscalisation DocTypes have been extended to store the FDMS-specific values:

- `Fiscal Provider Account`
  - device model headers
  - client certificate
  - client private key
  - server certificate
- `Fiscal Device`
  - device serial number
  - activation key
  - CSR
  - issued certificate
  - certificate expiry
  - operating mode
  - QR validation URL
  - last operation ID
  - fiscal day and receipt counters
- `Fiscal Day`
  - FDMS day status
  - operation ID
  - receipt global counter
  - server signature
  - close error code
- `Fiscal Document`
  - operation ID
  - receipt global number
  - receipt ID
  - QR data
  - verification URL
  - device/server signatures
  - request payload
  - provider response/error code

## Implementation Tasks

1. Build `ZimraFDMSProvider` separate from the demo provider.
2. Add HTTP client support for:
   - JSON requests
   - required device model headers
   - 30-second timeout
   - mutual TLS certificate/key files
   - structured error parsing
3. Add public setup calls:
   - `verify_taxpayer_information`
   - `register_device`
   - `get_server_certificate`
4. Add authenticated device calls:
   - `get_config`
   - `get_status`
   - `open_day`
   - `submit_receipt`
   - `close_day`
5. Implement CSR generation and secure key storage decision.
6. Map ERPNext `Sales Invoice` to FDMS receipt payload:
   - normal invoice -> fiscal invoice
   - return invoice -> credit note
   - taxes by line
   - payments by money type
   - receipt currency
   - receipt global number
7. Generate device signatures according to the FDMS signature rules.
8. Generate/store QR code data using FDMS QR rules.
9. Add retry and reconciliation actions on `Fiscal Document`.
10. Add a fiscalisation dashboard/list filter for pending, failed, and fiscalised invoices.

## Acceptance Criteria

- A ZIMRA test device can be registered from Omni.
- Omni can fetch FDMS config and device status.
- Omni can open a fiscal day.
- A submitted ERPNext Sales Invoice can be submitted to FDMS.
- FDMS receipt number, operation ID, QR data, and signatures are stored.
- Failed submissions remain auditable and retryable.
- Production use is blocked unless environment is Live, certificates are valid, and device status is active.

## Known Blockers

- Real ZIMRA device ID and activation key are required.
- Device model name/version must be known and registered.
- CSR/private key storage policy must be confirmed before live use.
- The sandbox must be reachable from the deployment environment.
- Signature generation must be validated against ZIMRA examples before live invoices are trusted.
