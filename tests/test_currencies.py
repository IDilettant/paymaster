import httpx
import pytest
from paymaster.currencies import BASE_CURRENCY, get_currencies_rates
from pytest_httpx import HTTPXMock

pytestmark = pytest.mark.asyncio


async def test_get_currencies_rates(httpx_mock: HTTPXMock):
    def custom_response(request: httpx.Request, *args, **kwargs):
        data = {
            'result': 'success', 'base_code': 'RUB',
            'conversion_rates': {BASE_CURRENCY.upper(): 1, 'USD': 0.01326},
        }
        return httpx.Response(
            status_code=200, json=data,
        )

    httpx_mock.add_callback(custom_response)
    api_key = 'some_api_key'
    cur_rate = await get_currencies_rates(api_key=api_key)
    assert cur_rate[0][0] == BASE_CURRENCY.upper()
    assert cur_rate[0][1] == 1
    assert cur_rate[1][0] == 'USD'
    assert cur_rate[1][1] == 0.01326
