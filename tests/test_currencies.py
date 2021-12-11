"""Currencies test module."""
import threading
import time
from datetime import datetime, timedelta

import freezegun
import pytest
from asyncpg import connect
from httpx import AsyncClient, Request, Response
from paymaster.app.data_schemas import OperationType
from paymaster.currencies import BASE_CURRENCY, get_currencies_rates
from paymaster.scripts.background_tasks import (
    _run_background_job,
    _set_task,
    fetch_and_update_data_currencies,
)
from pytest_httpx import HTTPXMock

pytestmark = pytest.mark.asyncio

USD_RATE = 0.0132
json_data = {
    'result': 'success', 'base_code': 'RUB',
    'conversion_rates': {BASE_CURRENCY.upper(): 1, 'USD': USD_RATE},
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
    assert cur_rate[1][1] == USD_RATE


async def test_background_currencies_update(
    httpx_mock: HTTPXMock,
    client: AsyncClient,
    dsn: str,
):
    db_conn = await connect(dsn)
    httpx_mock.add_callback(custom_response)
    api_key = 'some_api_key'
    await fetch_and_update_data_currencies(db_conn, api_key)
    now = datetime(1970, 1, 1, 00, 00)
    with freezegun.freeze_time(now) as frozen_date:
        job_thread = threading.Thread(
            target=_set_task, args=(_run_background_job, '00:00'),
        )
        job_thread.start()
        frozen_date.move_to(now + timedelta(days=1))
        time.sleep(1)
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
        response = await client.get(f'/balance/get/user_id/{user_id}?currency=USD')
        response = response.json()
        assert response['balance'] == round(USD_RATE, 2)
        job_thread.join(1.0)
