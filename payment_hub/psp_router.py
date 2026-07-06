"""PSP routing by currency, method, and region."""

from config.config import get_settings
from config.exceptions import PaymentError, CurrencyNotSupportedError
from payment_hub.models import PSPType

settings = get_settings()


class PSPRouter:
    CURRENCY_PSP_MAP = {
        "XOF": [PSPType.KORA, PSPType.FINCRA, PSPType.FLUTTERWAVE],
        "XAF": [PSPType.KORA, PSPType.FINCRA, PSPType.FLUTTERWAVE],
        "NGN": [PSPType.KORA, PSPType.FINCRA, PSPType.FLUTTERWAVE],
        "KES": [PSPType.KORA, PSPType.FINCRA],
        "GHS": [PSPType.KORA, PSPType.FINCRA, PSPType.FLUTTERWAVE],
        "ZAR": [PSPType.FINCRA, PSPType.STRIPE],
        "USD": [PSPType.FINCRA, PSPType.STRIPE],
        "EUR": [PSPType.FINCRA, PSPType.STRIPE],
        "GBP": [PSPType.FINCRA, PSPType.STRIPE],
    }

    REGION_PSP_PRIORITY = {
        "west_africa": [PSPType.KORA, PSPType.FLUTTERWAVE, PSPType.FINCRA],
        "east_africa": [PSPType.KORA, PSPType.FINCRA],
        "south_africa": [PSPType.FINCRA, PSPType.STRIPE],
        "international": [PSPType.STRIPE, PSPType.FINCRA],
    }

    @classmethod
    def select_psp(cls, currency: str, method: str | None = None, region: str = "west_africa", amount: str | None = None) -> PSPType:
        currency = currency.upper()
        if currency not in cls.CURRENCY_PSP_MAP:
            raise CurrencyNotSupportedError(f"Currency {currency} not supported")

        available = cls.CURRENCY_PSP_MAP[currency]
        priority = cls.REGION_PSP_PRIORITY.get(region, cls.REGION_PSP_PRIORITY["international"])

        candidates = [psp for psp in priority if psp in available]

        if not candidates:
            raise PaymentError(f"No PSP available for {currency} in {region}")

        for psp in candidates:
            if cls._has_credentials(psp):
                return psp

        raise PaymentError(f"No PSP with valid credentials for {currency}")

    @classmethod
    def _has_credentials(cls, psp: PSPType) -> bool:
        settings = get_settings()
        cred_map = {
            PSPType.KORA: settings.kora_api_key and settings.kora_secret_key,
            PSPType.FINCRA: settings.fincra_api_key and settings.fincra_secret_key,
            PSPType.FLUTTERWAVE: settings.flutterwave_public_key and settings.flutterwave_secret_key,
            PSPType.STRIPE: settings.stripe_publishable_key and settings.stripe_secret_key,
        }
        return bool(cred_map.get(psp))


psp_router = PSPRouter()
