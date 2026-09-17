import frappe


DESK_ROLES = {
	"Omni Operations Admin": 1,
	"Installation Coordinator": 1,
	"Technician": 1,
	"Fleet Manager": 1,
	"Customer Portal User": 0,
}


FULL_ACCESS = {
	"read": 1,
	"write": 1,
	"create": 1,
	"delete": 1,
	"submit": 0,
	"cancel": 0,
	"amend": 0,
	"report": 1,
	"export": 1,
	"import": 0,
	"share": 1,
	"print": 1,
	"email": 1,
}

READ_ONLY = {
	"read": 1,
	"write": 0,
	"create": 0,
	"delete": 0,
	"submit": 0,
	"cancel": 0,
	"amend": 0,
	"report": 1,
	"export": 1,
	"import": 0,
	"share": 0,
	"print": 1,
	"email": 1,
}

PORTAL_READ_ONLY = {
	**READ_ONLY,
	"export": 0,
	"share": 0,
	"email": 0,
}

WRITE_NO_DELETE = {
	**FULL_ACCESS,
	"delete": 0,
	"export": 0,
	"share": 0,
}


DOCTYPE_PERMISSIONS = {
	"Fleet Vehicle": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": WRITE_NO_DELETE,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Fleet Driver": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Vehicle Assignment": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Customer Fleet Profile": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Tracker Profile": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": WRITE_NO_DELETE,
	},
	"SIM Profile": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": WRITE_NO_DELETE,
	},
	"Tracker SIM Assignment": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": WRITE_NO_DELETE,
	},
	"Tracker Installation": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": WRITE_NO_DELETE,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Fleet Maintenance Work Order": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": WRITE_NO_DELETE,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Fleet Document": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": WRITE_NO_DELETE,
		"Technician": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Fleet Contract": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": FULL_ACCESS,
		"Installation Coordinator": READ_ONLY,
		"Technician": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Telematics Provider Account": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
	},
	"Telematics Discovered User": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
	},
	"Telematics Discovered Account": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
	},
	"Telematics Unit Link": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": WRITE_NO_DELETE,
		"Installation Coordinator": READ_ONLY,
		"Technician": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Telematics Sync Log": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
	},
	"Fiscal Provider Account": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
	},
	"Fiscal Device": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
	},
	"Fiscal Day": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
	},
	"Fiscal Document": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
		"Customer Portal User": PORTAL_READ_ONLY,
	},
	"Fiscal Sync Log": {
		"System Manager": FULL_ACCESS,
		"Omni Operations Admin": FULL_ACCESS,
		"Fleet Manager": READ_ONLY,
	},
}


def sync_omni_security():
	ensure_roles()
	ensure_doctype_permissions()
	frappe.db.commit()


def ensure_roles():
	for role_name, desk_access in DESK_ROLES.items():
		if frappe.db.exists("Role", role_name):
			frappe.db.set_value("Role", role_name, "desk_access", desk_access)
			frappe.db.set_value("Role", role_name, "disabled", 0)
			continue

		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": desk_access,
				"disabled": 0,
			}
		).insert(ignore_permissions=True)


def ensure_doctype_permissions():
	docperm_columns = set(frappe.db.get_table_columns("DocPerm"))

	for doctype, role_permissions in DOCTYPE_PERMISSIONS.items():
		if not frappe.db.exists("DocType", doctype):
			continue

		for role, settings in role_permissions.items():
			name = frappe.db.get_value(
				"DocPerm",
				{
					"parent": doctype,
					"parenttype": "DocType",
					"parentfield": "permissions",
					"permlevel": 0,
					"role": role,
				},
				"name",
			)

			values = {
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"permlevel": 0,
				"role": role,
				**{fieldname: value for fieldname, value in settings.items() if fieldname in docperm_columns},
			}

			if name:
				frappe.db.set_value("DocPerm", name, values, update_modified=False)
			else:
				values.update(
					{
						"doctype": "DocPerm",
						"name": frappe.generate_hash(length=10),
						"owner": frappe.session.user,
						"modified_by": frappe.session.user,
						"docstatus": 0,
						"idx": 0,
					}
				)
				frappe.get_doc(values).db_insert()

		frappe.clear_cache(doctype=doctype)
