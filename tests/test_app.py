"""Application test module."""
import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

first_user_id = 444
second_user_id = 555


async def test_app(client: AsyncClient):
    response = await client.post(f'/account/create/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_201_CREATED
    response = await client.post(f'/account/create/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_409_CONFLICT
