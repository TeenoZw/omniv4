from omni_operations.fiscalisation.providers.demo_zimra import DemoZimraFDMSProvider


PROVIDER_CLASSES = {
	"ZIMRA FDMS": DemoZimraFDMSProvider,
	"Other": DemoZimraFDMSProvider,
}


def get_provider(provider_account, fiscal_device):
	return PROVIDER_CLASSES.get(provider_account.provider, DemoZimraFDMSProvider)(
		provider_account, fiscal_device
	)
