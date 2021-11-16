from paymaster.app import API_KEY
from paymaster.currencies import get_currencies_rates, BASE_CURRENCY


async def test_get_currencies_rates():
    cur_rate = await get_currencies_rates(API_KEY)
    assert cur_rate[0][0] == BASE_CURRENCY
    assert cur_rate[0][1] == 1
