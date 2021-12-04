"""API routes module."""
import logging
from typing import Any, Dict, Tuple

from asyncpg import Connection
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from paymaster.currencies import BASE_CURRENCY
from paymaster.data_schemas import (
    Balance,
    Operation,
    PageOut,
    SortKey,
    Transaction,
)
from paymaster.db import (
    FRACTIONAL_VALUE,
    change_balance,
    create_acc,
    delete_acc,
    fetch_acc_history,
    get_balance,
    transfer_between_accs,
)
from paymaster.dependencies import get_connection_from_pool
from paymaster.exceptions import AccountError, BalanceValueError
from pydantic import PositiveInt

LOGGER = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    '/account/create/user_id/{user_id}',
    status_code=status.HTTP_201_CREATED,
)
async def create_user_acc(
    user_id: PositiveInt,
    connection: Connection = Depends(get_connection_from_pool),
) -> Response:
    """Create user account."""
    try:
        await create_acc(user_id=user_id, db_con=connection)
    except AccountError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Account already exists',
        )
    return Response(status_code=status.HTTP_201_CREATED)


@router.delete(
    '/account/delete/user_id/{user_id}',
    status_code=status.HTTP_200_OK,
)
async def delete_user_acc(
    user_id: PositiveInt,
    connection: Connection = Depends(get_connection_from_pool),
):
    """Delete user account."""
    try:
        await delete_acc(user_id=user_id, db_con=connection)
    except AccountError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account don't exists",
        )
    return Response(status_code=status.HTTP_200_OK)


@router.post('/balance/change', status_code=status.HTTP_201_CREATED)
async def change_user_balance(
    request: Operation,
    connection: Connection = Depends(get_connection_from_pool),
):
    """Change user balance."""
    try:
        await change_balance(
            user_id=request.user_id,
            qty_value=request.total,
            operation_type=request.operation.name,
            db_con=connection,
            description=request.description,
        )
    except AccountError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found',
        )
    except BalanceValueError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Insufficient funds on the debiting account',
        )
    return Response(status_code=status.HTTP_201_CREATED)


@router.post('/transactions/transfer', status_code=status.HTTP_201_CREATED)
async def transfer_between_users(
    request: Transaction,
    connection: Connection = Depends(get_connection_from_pool),
):
    """Transfer funds from one account to another."""
    if request.sender_id == request.recipient_id:
        exc = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sender and recipient accounts it's the same account",
        )
        LOGGER.warning(exc)
        raise exc
    try:
        await transfer_between_accs(
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            qty_value=request.total,
            description=request.description,
            db_con=connection,
        )
    except AccountError as exc:
        LOGGER.warning(exc)
        message = exc.args[0]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=message,
        )
    except BalanceValueError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Insufficient funds on the debiting account',
        )
    return Response(status_code=status.HTTP_201_CREATED)


@router.get(
    '/balance/get/user_id/{user_id}',
    response_model=Balance,
    status_code=status.HTTP_200_OK,
)
async def get_user_balance(
    user_id: int = Path(..., description='external user id'),
    currency: str = Query(
        BASE_CURRENCY,
        min_length=3,
        max_length=3,
        description='currency alias for balance value presentation',
    ),
    connection: Connection = Depends(get_connection_from_pool),
):
    """Get user account balance."""
    currency = currency.upper()
    try:
        balance = await get_balance(
            user_id=user_id,
            db_con=connection,
            convert_to=currency,
        )
    except AccountError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )
    return Balance(user_id=user_id, balance=balance, currency=currency)


@router.get(
    '/transactions/history/user_id/{user_id}',
    response_model=PageOut,
    status_code=status.HTTP_200_OK,
)
async def get_user_history(  # noqa: WPS211
    user_id: PositiveInt = Path(..., title='', description='external user id'),
    page_size: int = Query(20, gt=0, le=100, description='number of records per page'),  # noqa: WPS432 E501
    page_number: PositiveInt = Query(1, description='nuber of neccessary page'),
    order_by_date: SortKey = Query(None, description='sort order by transaction date'),  # noqa: E501
    order_by_total: SortKey = Query(None, description='sort order by transaction total value'),  # noqa: E501
    connection: Connection = Depends(get_connection_from_pool),
):
    """Get history of user account transactions."""
    try:
        history: Tuple[Dict[str, Any]] = await fetch_acc_history(
            user_id=user_id,
            db_con=connection,
            page_size=page_size,
            page_number=page_number,
            order_by_date=order_by_date,
            order_by_total=order_by_total,
        )
    except AccountError as exc:
        LOGGER.warning(exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found',
        )
    for record in history:
        record.update({'total': record['total'] / FRACTIONAL_VALUE})
    return PageOut(content=history)
