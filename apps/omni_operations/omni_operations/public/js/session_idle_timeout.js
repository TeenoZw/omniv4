(function () {
	const IDLE_LIMIT_MS = 15 * 60 * 1000;
	const WARNING_MS = 60 * 1000;
	let warningTimer;
	let logoutTimer;
	let dialog;

	function logout() {
		if (dialog) dialog.hide();
		frappe.call({
			method: "logout",
			callback: () => window.location.assign("/login?reason=inactive"),
			error: () => window.location.assign("/login?reason=inactive"),
		});
	}

	function showWarning() {
		let remaining = Math.floor(WARNING_MS / 1000);
		dialog = new frappe.ui.Dialog({
			title: __("Session ending soon"),
			fields: [{
				fieldname: "message",
				fieldtype: "HTML",
				options: `<p>${__("You will be signed out in {0} seconds because the admin session has been inactive.", [remaining])}</p>`,
			}],
			primary_action_label: __("Stay signed in"),
			primary_action() {
				dialog.hide();
				resetTimers();
			},
			secondary_action_label: __("Sign out now"),
			secondary_action: logout,
		});
		dialog.show();
		const countdown = setInterval(() => {
			remaining -= 1;
			const field = dialog && dialog.get_field("message");
			if (field) field.$wrapper.html(`<p>${__("You will be signed out in {0} seconds because the admin session has been inactive.", [Math.max(0, remaining)])}</p>`);
			if (remaining <= 0 || !dialog || !dialog.$wrapper.is(":visible")) clearInterval(countdown);
		}, 1000);
	}

	function resetTimers() {
		clearTimeout(warningTimer);
		clearTimeout(logoutTimer);
		warningTimer = setTimeout(showWarning, IDLE_LIMIT_MS - WARNING_MS);
		logoutTimer = setTimeout(logout, IDLE_LIMIT_MS);
	}

	function recordActivity() {
		if (!dialog || !dialog.$wrapper.is(":visible")) resetTimers();
	}

	frappe.ready(() => {
		["pointerdown", "keydown", "scroll", "touchstart"].forEach((event) =>
			document.addEventListener(event, recordActivity, { passive: true })
		);
		resetTimers();
	});
})();
