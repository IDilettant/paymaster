"""Application test module."""
import pytest
from fastapi import status
from httpx import AsyncClient
from paymaster.data_schemas import OperationType

pytestmark = pytest.mark.asyncio


async def test_app(client: AsyncClient):
    first_user_id = 444
    second_user_id = 555
    nonexistent_user = 321

    response = await client.post(f'/account/create/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_201_CREATED

    response = await client.post(f'/account/create/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_409_CONFLICT

    response = await client.post(f'/account/delete/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_205_RESET_CONTENT

    response = await client.post(f'/account/create/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_201_CREATED
    response = await client.post(
        '/balance/change',
        json={
            'operation': OperationType.replenishment,
            'user_id': first_user_id,
            'total': 100,
            'description': OperationType.replenishment,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await client.post(
        '/balance/change',
        json={
            'operation': OperationType.replenishment,
            'user_id': nonexistent_user,
            'total': 100,
            'description': OperationType.replenishment,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await client.post(
        '/balance/change',
        json={
            'operation': OperationType.withdraw,
            'user_id': first_user_id,
            'total': 999,
            'description': OperationType.withdraw,
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = await client.post(
        '/balance/change',
        json={
            'operation': OperationType.withdraw,
            'user_id': first_user_id,
            'total': 10,
            'description': OperationType.withdraw,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await client.post(
        '/transactions/transfer',
        json={
            'sender_id': first_user_id,
            'recipient_id': first_user_id,
            'total': 40,
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = await client.post(
        '/transactions/transfer',
        json={
            'sender_id': first_user_id,
            'recipient_id': nonexistent_user,
            'total': 40,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await client.post(
        '/transactions/transfer',
        json={
            'sender_id': nonexistent_user,
            'recipient_id': first_user_id,
            'total': 40,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    await client.post(f'/account/create/user_id/{second_user_id}')
    response = await client.post(
        '/transactions/transfer',
        json={
            'sender_id': first_user_id,
            'recipient_id': second_user_id,
            'total': 40,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await client.post(
        '/transactions/transfer',
        json={
            'sender_id': first_user_id,
            'recipient_id': second_user_id,
            'total': 999,
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = await client.get(f'/balance/get/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_200_OK
    response = response.json()
    assert response['balance'] == 50
    response = await client.get(f'/balance/get/user_id/{second_user_id}')
    assert response.status_code == status.HTTP_200_OK
    response = response.json()
    assert response['balance'] == 40
    response = await client.get(f'/balance/get/user_id/{nonexistent_user}')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await client.get(f'/transactions/history/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_200_OK
    response = response.json()['content']
    assert response[0]['deal_with'] == first_user_id
    assert response[0]['description'] == 'replenishment'
    assert response[0]['total'] == 100
    assert response[1]['deal_with'] == first_user_id
    assert response[1]['description'] == 'withdraw'
    assert response[1]['total'] == -10
    assert response[2]['deal_with'] == second_user_id
    assert response[2]['description'] == 'outcoming payment'
    assert response[2]['total'] == -40
    response = await client.get(f'/transactions/history/user_id/{nonexistent_user}')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await client.post(f'/account/delete/user_id/{first_user_id}')
    assert response.status_code == status.HTTP_205_RESET_CONTENT
