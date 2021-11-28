import asyncio
import os
from typing import List, Optional
import asyncpg

from asyncpg import Connection
import status 
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Query, Path, HTTPException, Response, status, APIRouter
from pydantic import PositiveInt

from paymaster.currencies import BASE_CURRENCY, get_currencies_rates
from paymaster.db import (
    get_balance,
    transfer_between_accs,
    create_acc,
    delete_acc,
    change_balance,
    fetch_acc_history,
    DSN, 
    _update_currencies,
)
from paymaster.data_schemas import Balance, Transaction, Operation, PageOut
from paymaster.dependencies import get_connection_from_pool
from paymaster.exceptions import AccountError, BalanceValueError

load_dotenv()

API_KEY = os.getenv('API_KEY')

router = APIRouter()


@app.on_event('startup')
async def startup_event():
    app.state.pool = await asyncpg.create_pool(DSN)


@app.on_event('shutdown')
async def shutdown_event():
    await app.state.pool.close()


@app.post('/account/create/user_id/{user_id}/', status_code=status.HTTP_201_CREATED)
async def create_user_acc(
        user_id: PositiveInt, 
        connection: Connection = Depends(get_connection_from_pool),
):
    try:
        await create_acc(user_id=user_id, db_con=connection)
    except AccountError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')
    return Response(status_code=status.HTTP_201_CREATED)


@app.post('/account/delete/user_id/{user_id}/', status_code=status.HTTP_205_RESET_CONTENT)
async def delete_user_acc(
        user_id: PositiveInt,
        connection: Connection = Depends(get_connection_from_pool),
):
    await delete_acc(user_id=user_id, db_con=connection)
    return Response(status_code=status.HTTP_205_RESET_CONTENT)


@app.post("/balance/change/", status_code=status.HTTP_201_CREATED)
async def change_user_balance(
        request: Operation,
        connection: Connection = Depends(get_connection_from_pool),
):
    try:
        await change_balance(
            user_id=request.user_id, 
            qty_value=request.total, 
            operation_type=request.operation.name, 
            db_con=connection, 
            description=request.description,
        )
    except AccountError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    except BalanceValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Insufficient funds on the debiting account')
    return Response(status_code=status.HTTP_201_CREATED)


@app.post("/transactions/transfer/", status_code=status.HTTP_201_CREATED)
async def transfer_between_users(
        request: Transaction,
        connection: Connection = Depends(get_connection_from_pool),
):
    try:
        await transfer_between_accs(
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            qty_value=request.total,
            description=request.description,
            db_con=connection,
        )
    except AccountError as exc:
        message = exc.args[0]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    except BalanceValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Insufficient funds on the debiting account')
    return Response(status_code=status.HTTP_201_CREATED)


@app.get('/balance/get/user_id/{user_id}/', response_model=Balance, status_code=status.HTTP_200_OK)
async def get_user_balance(
        user_id: int = Path(..., title='', description=''),
        currency: Optional[str] = Query(BASE_CURRENCY, min_length=3, max_length=3, description=''),
        connection: Connection = Depends(get_connection_from_pool),
):
    try:
        balance = await get_balance(user_id=user_id, db_con=connection, convert_to=currency)
    except AccountError:
        raise HTTPException(status_code=404, detail="User not found")
    return Balance(user_id=user_id, balance=balance, currency=currency)


@app.get("/transactions/history/user_id/{user_id}", response_model=PageOut, status_code=status.HTTP_200_OK)
async def get_user_history(
        user_id: PositiveInt = Path(..., title='', description=''), 
        page_size: int = Query(20, gt=0, le=100, description=''),
        page_number: PositiveInt = Query(1, description=''),
        order_by: List[str] = Query(None, description='', regex="^fixedquery$"),  # TODO: regex validation
        connection: Connection = Depends(get_connection_from_pool),
):
    try:
        history = await fetch_acc_history(
            user_id=user_id, 
            db_con=connection,
            page_size=page_size,
            page_number=page_number,
            order_by=order_by,
        )
    except AccountError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for record in history:
        record.update({'total': record['total'] / 100})
    return PageOut(
        page_number=page_number, 
        content=history,
    )


async def main():
    connection = await asyncpg.connect(dsn=DSN)
    # cur_rate = await get_currencies_rates(API_KEY, BASE_CURRENCY)
    # await _update_currencies(cur_rate, connection)
    print(await get_balance(111, db_con=connection))


if __name__ == '__main__':
    asyncio.run(main())
