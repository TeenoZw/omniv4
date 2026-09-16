from omni_operations.omni_setup.branding import apply_omni_branding
from omni_operations.omni_setup.desk import configure_omni_focused_desk
from omni_operations.omni_setup.hub_companies import sync_hub_companies
from omni_operations.omni_setup.permissions import sync_omni_security
from omni_operations.omni_setup.post_migration import backfill_tracker_sim_assignments
from omni_operations.omni_setup.quote_add_ons import sync_quote_add_ons


def after_install():
	apply_omni_branding()
	sync_omni_security()
	sync_hub_companies()
	sync_quote_add_ons()
	configure_omni_focused_desk()


def after_migrate():
	apply_omni_branding()
	sync_omni_security()
	sync_hub_companies()
	backfill_tracker_sim_assignments()
	sync_quote_add_ons()
	configure_omni_focused_desk()
