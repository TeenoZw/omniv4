import frappe

from omni_operations.telematics.providers.base import BaseTelematicsProvider
from omni_operations.telematics.providers.custom_api import CustomAPITelematicsProvider
from omni_operations.telematics.providers.demo import DemoTelematicsProvider
from omni_operations.telematics.providers.wialon import WialonTelematicsProvider


PROVIDER_CLASSES = {
	"Other": DemoTelematicsProvider,
	"Custom API": CustomAPITelematicsProvider,
	"Wialon": WialonTelematicsProvider,
}


def get_provider(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider_class = PROVIDER_CLASSES.get(provider_account.provider, BaseTelematicsProvider)
	return provider_class(provider_account)
