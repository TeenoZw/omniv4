# 03 – API Surface (Current Scope)

This document lists the active API endpoints after the Wialon pivot. Tracking, telemetry, and analytics live in Wialon and are not exposed here.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All non-public endpoints require a bearer token:

```
Authorization: Bearer <token>
```

## Users

### Register (admin only)

```
POST /users/register
```

### Login

```
POST /users/login
```

### Get user

```
GET /users/{user_id}
```

## Enquiries (public + admin)

### Create enquiry (public)

```
POST /enquiries
```

### List enquiries (admin)

```
GET /enquiries?status=new
```

### Update enquiry (admin)

```
PATCH /enquiries/{id}
```

## Hubs (admin)

### List hubs

```
GET /hubs
```

### Get hub

```
GET /hubs/{id}
```

### Create hub

```
POST /hubs
```

### Update hub

```
PATCH /hubs/{id}
```

### Create hub user

```
POST /hubs/{id}/users
```

## Devices (admin + technician)

### List devices

```
GET /devices
```

### Get device

```
GET /devices/{id}
```

### Update device status

```
PATCH /devices/{id}/status
```

### Update device details

```
PATCH /devices/{id}
```

### Assign device

```
POST /devices/{id}/assign
```

## Health

```
GET /health
```

## Notes

- Tracking and telemetry are handled in Wialon.
- If you need an endpoint added, update `docs/06_roadmap.md` and open a task in `docs/10_implementation_checklist.md`.
