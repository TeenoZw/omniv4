FROM frappe/erpnext:v15.125.0@sha256:18127922c64b2e3d009989384bc6a61043d5e41a82ae9f956d03dedcf6478d65

USER root
COPY --chown=frappe:frappe apps/omni_operations /home/frappe/frappe-bench/apps/omni_operations
USER frappe
WORKDIR /home/frappe/frappe-bench

RUN . env/bin/activate \
	&& pip install --no-cache-dir -e apps/omni_operations \
	&& printf "frappe\nerpnext\nomni_operations\n" > sites/apps.txt \
	&& bench build --app omni_operations \
	&& mkdir -p assets/omni_operations \
	&& cp -a apps/omni_operations/omni_operations/public/. assets/omni_operations/
