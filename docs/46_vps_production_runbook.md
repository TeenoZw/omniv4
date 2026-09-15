# 46 - VPS Production Runbook

## Purpose

Use this runbook when deploying Omni v4 Frappe/ERPNext to a normal Linux VPS instead of Render.

Recommended minimum VPS:

- Ubuntu 22.04 LTS or 24.04 LTS
- 2 vCPU minimum
- 4 GB RAM minimum
- 80 GB storage minimum
- Docker and Docker Compose plugin

## Deployment Shape

```text
Cloudflare DNS
├── www.omnilogistics.co.zw      -> Cloudflare Pages public site
├── portal-v4.omnilogistics.co.zw -> Cloudflare Pages portal preview
└── admin-v4.omnilogistics.co.zw -> VPS public IP

VPS
├── Frappe/ERPNext + omni_operations
├── MariaDB volume
├── Redis volume/cache
├── scheduler and workers
└── backup directory
```

## Required Secrets

Keep these out of Git:

```text
FRAPPE_SITE_NAME=admin-v4.omnilogistics.co.zw
ADMIN_PASSWORD=<strong password>
MYSQL_ROOT_PASSWORD=<strong password>
MARIADB_ROOT_PASSWORD=<same or separate strong password>
TELEMATICS_PROVIDER_TOKEN=<provider token>
SMTP credentials
ZIMRA credentials/certificates, when available
```

## Smoke Checks

After deployment:

```bash
scripts/production_smoke_check.sh https://admin-v4.omnilogistics.co.zw
```

Inside the Frappe container or bench:

```bash
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_desk_focus_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_onboarding_job_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_tracker_sim_assignment_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_portal_api_smoke_checks
```

## Backups

Run:

```bash
FRAPPE_CONTAINER=omniv4-frappe \
FRAPPE_SITE_NAME=admin-v4.omnilogistics.co.zw \
BACKUP_DIR=/srv/omniv4/backups \
scripts/frappe_backup.sh
```

Minimum launch rule:

- At least one manual backup must be created.
- At least one restore rehearsal must be completed before real customer cutover.
- Keep daily backups for at least 14 days during the first launch period.

## Launch Hardening Checklist

- Disable or rotate all demo/test passwords.
- Confirm only required users have `System Manager`.
- Confirm customer portal users have customer-scoped access only.
- Configure SMTP and send a test email.
- Confirm scheduler is enabled.
- Confirm workers are running.
- Confirm MariaDB data survives restart.
- Confirm backups copy off the VPS or to a second storage location.
- Put Cloudflare proxy in front of public hostnames after first direct smoke check.
