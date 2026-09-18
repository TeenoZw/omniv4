FROM frappe/erpnext:v15.119.2

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
