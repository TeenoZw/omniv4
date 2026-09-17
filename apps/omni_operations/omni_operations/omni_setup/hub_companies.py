import frappe


DEFAULT_COUNTRY = "Zimbabwe"
DEFAULT_CURRENCY = "USD"
DEFAULT_OMNI_COMPANY = "Omni Industrial Solutions"
DEFAULT_OMNI_ABBR = "OIS"
PHYSICAL_WAREHOUSES = ("Kwekwe Warehouse", "Hwange Warehouse")


def clean(value):
	return (value or "").strip()


def ensure_required_warehouse_types():
	"""Create ERPNext reference data required during first Company insertion."""
	if frappe.db.exists("DocType", "Warehouse Type") and not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(ignore_permissions=True)


def is_hub_name(value):
	return bool(clean(value).lower().endswith(" hub"))


def get_hub_customers():
	hub_names = set()

	for doctype in ("Customer Fleet Profile", "Fleet Vehicle", "Tracker Installation"):
		if not frappe.db.exists("DocType", doctype):
			continue
		if not any(field.fieldname == "customer" for field in frappe.get_meta(doctype).fields):
			continue
		for row in frappe.get_all(doctype, fields=["customer"], limit_page_length=1000):
			if row.customer and frappe.db.exists("Customer", row.customer):
				hub_names.add(row.customer)

	for customer in frappe.get_all("Customer", fields=["name"], limit_page_length=1000):
		if is_hub_name(customer.name):
			hub_names.add(customer.name)

	return sorted(hub_names)


def get_or_create_business_customer_group():
	group_name = "Business"
	if frappe.db.exists("Customer Group", group_name):
		return group_name

	parent_group = frappe.db.get_value("Customer Group", {"is_group": 1}, "name") or "All Customer Groups"
	frappe.get_doc(
		{
			"doctype": "Customer Group",
			"customer_group_name": group_name,
			"parent_customer_group": parent_group,
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return group_name


def get_or_create_zimbabwe_territory():
	territory = DEFAULT_COUNTRY
	if frappe.db.exists("Territory", territory):
		return territory

	parent_territory = frappe.db.get_value("Territory", {"is_group": 1}, "name") or "All Territories"
	frappe.get_doc(
		{
			"doctype": "Territory",
			"territory_name": territory,
			"parent_territory": parent_territory,
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return territory


def ensure_omni_company():
	ensure_required_warehouse_types()
	existing = frappe.db.exists("Company", DEFAULT_OMNI_COMPANY) or frappe.defaults.get_global_default("company")
	if existing:
		company = frappe.get_doc("Company", existing)
		company.default_currency = DEFAULT_CURRENCY
		company.country = DEFAULT_COUNTRY
		company.is_group = 0
		company.save(ignore_permissions=True)
		return company.name

	company = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": DEFAULT_OMNI_COMPANY,
			"abbr": DEFAULT_OMNI_ABBR,
			"default_currency": DEFAULT_CURRENCY,
			"country": DEFAULT_COUNTRY,
			"create_chart_of_accounts_based_on": "Standard Template",
			"chart_of_accounts": "Standard",
			"is_group": 0,
		}
	)
	company.insert(ignore_permissions=True)
	return company.name


def ensure_hub_company(hub_customer=None):
	"""Compatibility shim: hubs are customers, not accounting companies."""
	return ensure_omni_company()


def get_company_for_hub_customer(customer):
	return get_default_hub_company()


def get_default_hub_company():
	return ensure_omni_company()


def ensure_customer_is_business_hub(customer):
	if not frappe.db.exists("Customer", customer):
		return

	doc = frappe.get_doc("Customer", customer)
	doc.customer_type = "Company"
	doc.customer_group = get_or_create_business_customer_group()
	doc.territory = get_or_create_zimbabwe_territory()
	doc.disabled = 0
	doc.save(ignore_permissions=True)


def ensure_customer_fleet_profile(customer, company):
	company = company or get_default_hub_company()
	if not frappe.db.exists("Customer Fleet Profile", customer):
		doc = frappe.get_doc(
			{
				"doctype": "Customer Fleet Profile",
				"customer": customer,
				"company": company,
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	doc = frappe.get_doc("Customer Fleet Profile", customer)
	doc.company = company
	doc.status = "Active"
	doc.save(ignore_permissions=True)
	return doc.name


def update_company_fields_for_customer(customer, company):
	company = company or get_default_hub_company()
	updated = []
	for doctype in (
		"Fleet Vehicle",
		"Tracker Installation",
		"Vehicle Assignment",
		"Fleet Driver",
		"Fleet Document",
		"Fleet Contract",
		"Fleet Maintenance Work Order",
	):
		if not frappe.db.exists("DocType", doctype):
			continue

		fieldnames = {field.fieldname for field in frappe.get_meta(doctype).fields}
		if "customer" not in fieldnames or "company" not in fieldnames:
			continue

		names = frappe.get_all(doctype, filters={"customer": customer}, pluck="name", limit_page_length=1000)
		for name in names:
			frappe.db.set_value(doctype, name, "company", company, update_modified=False)
			updated.append({"doctype": doctype, "name": name})
	return updated


def ensure_physical_warehouses(company=None):
	company = company or get_default_hub_company()
	abbr = frappe.db.get_value("Company", company, "abbr")
	parent_warehouse = f"All Warehouses - {abbr}"
	if not frappe.db.exists("Warehouse", parent_warehouse):
		parent_warehouse = frappe.db.get_value("Warehouse", {"company": company, "is_group": 1}, "name")

	created = []
	for warehouse_name in PHYSICAL_WAREHOUSES:
		existing = frappe.db.exists("Warehouse", {"warehouse_name": warehouse_name, "company": company})
		if existing:
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": warehouse_name,
				"company": company,
				"parent_warehouse": parent_warehouse,
				"is_group": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	return created


def detach_system_provider_accounts():
	if not frappe.db.exists("DocType", "Telematics Provider Account"):
		return []

	updated = []
	for account in frappe.get_all(
		"Telematics Provider Account",
		filters={"account_scope": "System-wide"},
		fields=["name", "company"],
	):
		if account.company:
			frappe.db.set_value(
				"Telematics Provider Account",
				account.name,
				"company",
				None,
				update_modified=False,
			)
			updated.append(account.name)
	return updated


@frappe.whitelist()
def sync_hub_companies():
	updated = []
	record_updates = []
	hubs = get_hub_customers()
	default_company = get_default_hub_company()
	created_warehouses = ensure_physical_warehouses(default_company)

	for hub in hubs:
		ensure_customer_is_business_hub(hub)
		ensure_customer_fleet_profile(hub, default_company)
		record_updates.extend(update_company_fields_for_customer(hub, default_company))
		updated.append(hub)

	if default_company:
		frappe.db.set_single_value("Global Defaults", "default_company", default_company)
		frappe.defaults.set_global_default("company", default_company)
		frappe.defaults.set_user_default("Company", default_company, "Administrator")

	system_provider_accounts = detach_system_provider_accounts()
	frappe.db.commit()
	return {
		"hubs": hubs,
		"created_companies": [],
		"updated_customers": updated,
		"default_company": default_company,
		"created_warehouses": created_warehouses,
		"system_provider_accounts_detached": system_provider_accounts,
		"record_updates": record_updates,
	}


def _company_has_transactions(company):
	transaction_checks = (
		("GL Entry", "company"),
		("Sales Invoice", "company"),
		("Purchase Invoice", "company"),
		("Payment Entry", "company"),
		("Stock Ledger Entry", "company"),
		("Stock Entry", "company"),
	)
	for doctype, fieldname in transaction_checks:
		if not frappe.db.exists("DocType", doctype):
			continue
		if frappe.db.count(doctype, {fieldname: company}):
			return True
	return False


@frappe.whitelist()
def remove_generated_hub_companies():
	default_company = get_default_hub_company()
	hub_company_names = [hub for hub in get_hub_customers() if frappe.db.exists("Company", hub)]
	removed = []
	skipped = []

	for company in hub_company_names:
		if company == default_company:
			skipped.append({"company": company, "reason": "default company"})
			continue
		if _company_has_transactions(company):
			skipped.append({"company": company, "reason": "has accounting or stock transactions"})
			continue

		try:
			frappe.delete_doc("Company", company, ignore_permissions=True, force=True)
			removed.append(company)
		except Exception as exc:
			skipped.append({"company": company, "reason": str(exc)})

	frappe.db.commit()
	return {"removed": removed, "skipped": skipped}
