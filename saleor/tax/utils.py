from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..account.models import Address
    from ..channel.models import Channel
    from .models import TaxConfiguration, TaxConfigurationPerCountry


def get_display_gross_prices(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
):
    return (
        country_tax_configuration.display_gross_prices
        if country_tax_configuration
        else channel_tax_configuration.display_gross_prices
    )


def get_tax_country(
    channel: "Channel",
    is_shipping_required: bool,
    shipping_address: Optional["Address"] = None,
    billing_address: Optional["Address"] = None,
):
    if shipping_address and is_shipping_required:
        return shipping_address.country.code

    if billing_address and not is_shipping_required:
        return billing_address.country.code

    return channel.default_country.code
