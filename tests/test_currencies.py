import time
from datetime import timedelta, datetime

import freezegun
import pytest
from httpx import AsyncClient, Request, Response
from paymaster.app.data_schemas import OperationType
from paymaster.currencies import BASE_CURRENCY, get_currencies_rates
from pytest_httpx import HTTPXMock

from paymaster.scripts.background_tasks import set_task, run_background_job, run_continuously

pytestmark = pytest.mark.asyncio

usd_rate = 0.06231
json_data = {
    'result': 'success', 'base_code': 'RUB',
    'conversion_rates': {BASE_CURRENCY.upper(): 1, 'USD': usd_rate},
}


def custom_response(request: Request, *args, **kwargs):
    return Response(
        status_code=200, json=json_data,
    )


async def test_get_currencies_rates(httpx_mock: HTTPXMock):
    httpx_mock.add_callback(custom_response)
    api_key = 'some_api_key'
    cur_rate = await get_currencies_rates(api_key=api_key)
    assert cur_rate[0][0] == BASE_CURRENCY.upper()
    assert cur_rate[0][1] == 1
    assert cur_rate[1][0] == 'USD'
    assert cur_rate[1][1] == usd_rate


# @freezegun.freeze_time('1970-01-01 00:00')
async def test_background_currencies_update(
    httpx_mock: HTTPXMock,
    client: AsyncClient,
):
    # with freezegun.freeze_time('1970-01-01 00:00'):
    now = datetime(2020, 1, 1, 10, 31)
    with freezegun.freeze_time(now) as frozen_date:
        httpx_mock.add_callback(custom_response)
        set_task(run_background_job, '10:30')
        frozen_date.move_to(now + timedelta(days=1))
        time.sleep(5)
        user_id = 42
        await client.post(f'/account/create/user_id/{user_id}')
        await client.post(
            '/balance/change',
            json={
                'operation': OperationType.replenishment,
                'user_id': user_id,
                'total': 1,
                'description': OperationType.replenishment,
            },
        )
        response = await client.get(f'/balance/get/user_id/{user_id}?currency=usd')
        response = response.json()
        assert response['balance'] == round(usd_rate, 2)
