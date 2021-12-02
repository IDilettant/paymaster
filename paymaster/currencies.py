"""Currencies module."""
from typing import Any, List, Tuple

import httpx

BASE_CURRENCY = 'rub'


async def get_currencies_rates(
    api_key: str,
    base_currency: str = BASE_CURRENCY,
) -> List[Tuple[Any]]:
    """Get currencies rates from remote server.

    Args:
        api_key: service access key
        base_currency: base currency for calculate rates

    Returns:
        currencies rates
    """
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        response = resp.json()
        cur_rates = response['conversion_rates']
        return [
            tuple(currency, cur_rates[currency]) for currency in cur_rates
        ]
