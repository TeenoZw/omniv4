FROM frappe/erpnext:v15

USER root

COPY --chown=frappe:frappe erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations /home/frappe/frappe-bench/apps/omni_operations
COPY --chown=frappe:frappe deploy/render/start-frappe-staging.sh /home/frappe/start-frappe-staging.sh

RUN chmod 755 /home/frappe/start-frappe-staging.sh

USER frappe
WORKDIR /home/frappe/frappe-bench

RUN . env/bin/activate \
	&& pip install --no-cache-dir -e apps/omni_operations \
	&& printf "frappe\nerpnext\nomni_operations\n" > sites/apps.txt \
	&& bench build --app omni_operations

EXPOSE 8000

CMD ["/home/frappe/start-frappe-staging.sh"]
