frappe.listview_settings["Telematics Discovered User"] = {
	add_fields: ["review_status", "is_disabled", "customer"],
	get_indicator(doc) {
		if (doc.review_status === "Needs Review") {
			return [__("Needs Review"), "orange", "review_status,=,Needs Review"];
		}
		if (doc.review_status === "Mapped to Customer") {
			return [__("Mapped"), "green", "review_status,=,Mapped to Customer"];
		}
		return [__(doc.review_status || "Reviewed"), "gray", `review_status,=,${doc.review_status}`];
	},
};
