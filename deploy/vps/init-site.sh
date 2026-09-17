#!/usr/bin/env bash
set -euo pipefail

cd /home/frappe/frappe-bench
site="${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME is required}"

if [ ! -d "sites/$site" ]; then
	bench new-site "$site" \
		--mariadb-user-host-login-scope='%' \
		--admin-password="$ADMIN_PASSWORD" \
		--db-root-username=root \
		--db-root-password="$MARIADB_ROOT_PASSWORD" \
		--install-app erpnext \
		--set-default
	bench --site "$site" install-app omni_operations
else
	bench --site "$site" migrate
fi

bench use "$site"
bench --site "$site" set-config host_name "https://$site"
bench --site "$site" set-config developer_mode 0
bench --site "$site" enable-scheduler

