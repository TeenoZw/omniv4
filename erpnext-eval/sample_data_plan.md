# ERPNext Sample Data Plan

Create this sample data during `A-007`.

## Company

- Company Name: Omni Demo Operations
- Country: Zimbabwe
- Currency: USD
- Fiscal Year: current year

## Customers

- Acme Transport
- Harare Mining Logistics
- City Utilities Fleet

## Suppliers

- Tracker Hardware Supplier
- SIM Connectivity Supplier
- Vehicle Parts Supplier

## Items

| Item | Type | Stocked | Notes |
| --- | --- | --- | --- |
| Fleet Monitoring Monthly Service | Service | No | Recurring billable service. |
| Tracker Device | Product | Yes | Serialized hardware. |
| SIM Card | Product | Yes | Serialized or batched depending on ERPNext fit. |
| Installation Labour | Service | No | One-time installation line. |
| Maintenance Labour | Service | No | Billable workshop/field labour. |
| Vehicle Battery | Product | Yes | Example maintenance part. |

## Warehouses

- Main Warehouse
- Technician Stock
- Faulty Returns

## Commercial Test Flow

```text
Customer
-> Quotation
-> Sales Order
-> Sales Invoice
-> Payment Entry
```

## Purchasing Test Flow

```text
Supplier
-> Purchase Order
-> Purchase Receipt
-> Purchase Invoice
-> Payment Entry
```

## Fleet Test Flow

```text
Customer
-> Vehicle
-> Tracker Device
-> SIM Card
-> Wialon Unit Link
-> Customer Fleet Profile
```

