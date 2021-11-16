from typing import Any, List, Tuple

import aiohttp

BASE_CURRENCY = 'RUB'


async def get_currencies_rates(
        api_key: str,
        base_currency: str = BASE_CURRENCY,
) -> List[Tuple[Any]]:
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
    async with aiohttp.request(method='get', url=url, raise_for_status=True) as resp:
        response = await resp.json()
        cur_rates = response['conversion_rates']
        return [tuple([currency, cur_rates[currency]]) for currency in cur_rates]
