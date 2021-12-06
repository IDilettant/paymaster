"""Currencies module."""
import logging
from typing import List, Optional, Tuple

import httpx
from fastapi import HTTPException

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
    """
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except HTTPException:
            raise 
        response = resp.json()
        cur_rates = response['conversion_rates']
        return [
            (currency, cur_rates[currency]) for currency in cur_rates
        ]
