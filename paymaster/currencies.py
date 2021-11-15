from typing import List, Tuple

import aiohttp


async def get_currencies_rates(
        api_key: str, 
        base_currency: str = 'RUB',
) -> List[Tuple]:
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
    async with aiohttp.request(method='get', url=url, raise_for_status=True) as resp:
        response = await resp.json()
        cur_rates = response['conversion_rates']
        return [(currency, cur_rates[currency]) for currency in cur_rates]
