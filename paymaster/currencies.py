"""Currencies module."""
import logging
from typing import List, Optional, Tuple

import httpx
from paymaster.exceptions import CurrencyError

BASE_CURRENCY = 'rub'
LOGGER = logging.getLogger(__name__)


async def get_currencies_rates(  # noqa: WPS234
    api_key: Optional[str],
    base_currency: str = BASE_CURRENCY,
) -> List[Tuple[str, float]]:
    """Get currencies rates from remote server.

    Args:
        api_key: service access key
        base_currency: base currency for calculate rates

    Returns:
        currencies rates

    Raises:
        CurrencyError: currency rates source unavailable
    """
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise CurrencyError('Currency rates source unavailable') from exc
        response = resp.json()
        cur_rates = response['conversion_rates']
        return [
            (currency, cur_rates[currency]) for currency in cur_rates
        ]
