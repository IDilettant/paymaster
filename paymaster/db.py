"""Database module."""
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

import asyncpg
from asyncpg import Connection
from paymaster.exceptions import AccountError, BalanceValueError, CurrencyError

FRACTIONAL_VALUE = Decimal(100)


async def create_acc(user_id: int, db_con: Connection) -> None:
    query = """ INSERT INTO accounts (user_id) VALUES ($1);"""
    if await _has_account(user_id, db_con):
        raise AccountError(f'Account with id <{user_id}> already exists')
    else:
        await db_con.execute(query, user_id)


async def delete_acc(user_id: int, db_con: Connection) -> None:
    tx_query = """  DELETE FROM transactions
                    WHERE account_id = (
                        SELECT id FROM accounts
                        WHERE user_id = $1
                    );"""
    acc_query = """ DELETE FROM accounts
                    WHERE user_id = ($1);"""
    async with db_con.transaction():
        await db_con.execute(tx_query, user_id)
        await db_con.execute(acc_query, user_id)


async def change_balance(
        user_id: int,
        qty_value: Decimal,  # What if negative?
        operation_type: str,
        db_con: Connection,
        description: Optional[str] = None,
):
    if operation_type == 'credit':
        await _crediting_balance(
            user_id=user_id,
            qty_value=qty_value,
            db_con=db_con,
            description=description,
        )
    elif operation_type == 'debit':
        await _debiting_balance(
            user_id=user_id,
            qty_value=qty_value,
            db_con=db_con,
            description=description,
        )


async def transfer_between_accs(
        sender_id: int,
        recipient_id: int,
        qty_value: Decimal,
        db_con: Connection,
        description: Optional[str] = None,
) -> None:
    async with db_con.transaction():
        await _debiting_balance(
            user_id=sender_id,
            deal_with=recipient_id,
            qty_value=qty_value,
            description=description,
            db_con=db_con,
        )
        await _crediting_balance(
            user_id=recipient_id,
            deal_with=sender_id,
            qty_value=qty_value,
            description=description,
            db_con=db_con,
        )


async def get_balance(user_id: int, db_con: Connection, convert_to: Optional[str] = None) -> Decimal:
    if await _has_account(user_id, db_con):
        balance = await _compute_balance(user_id, db_con) / FRACTIONAL_VALUE
        cur_rate = 1 if convert_to is None else await _fetch_currency_rate(cur_name=convert_to, db_con=db_con)
        # Should I convert here or in app?
        return Decimal(round(balance * cur_rate, 2))
    else:
        raise AccountError(f'Has no registered account with id: {user_id}')


async def fetch_acc_history(
        user_id: int,
        db_con: Connection,
        page_number: int = 1,
        page_size: int = 20,
        order_by: Optional[List[str]] = None,
) -> Tuple[Dict]:
    order_by = ['-date'] if order_by is None else order_by
    offset = (page_number - 1) * page_size
    primary_key, additional_key, coma = await _get_sort_keys(order_by)
    query: str = f"""   SELECT DATE(created_at) AS date, deal_with, description, qty_change as total
                            FROM transactions
                            WHERE account_id = (
                                SELECT id FROM accounts WHERE user_id = $1
                            )
                            ORDER BY {primary_key}{coma} {additional_key}
                            OFFSET $2 LIMIT $3;"""
    history = await db_con.fetch(query, user_id, offset, page_size)

    if history:
        return tuple(map(dict, history))
    else:
        raise AccountError(f'Has no registered account with id: {user_id}')


async def update_currencies(cur_rates: List[Tuple[Any]], db_con: Connection) -> None:  # TODO: make updating regular
    query = """ INSERT INTO currencies (cur_name, rate_to_base)
                VALUES ($1, $2)
                ON CONFLICT (cur_name)
                DO UPDATE SET rate_to_base = $2
                WHERE currencies.cur_name = $1;"""
    await db_con.executemany(query, cur_rates)


async def _crediting_balance(
        user_id: int,
        qty_value: Decimal,
        db_con: Connection,
        deal_with: Optional[int] = None,
        description: Optional[str] = None,
) -> None:
    deal_with = user_id if deal_with is None else deal_with
    description = 'balance replenishment' if description is None else description
    fractional_qty_value = int(qty_value * FRACTIONAL_VALUE)
    query = """ INSERT INTO transactions (
                    account_id, deal_with, description, qty_change
                )
                VALUES (
                    (SELECT id FROM accounts WHERE user_id = $1), $2, $3, $4
                );"""
    async with db_con.transaction():  # or privacy level?
        try:
            await db_con.execute(query, user_id, deal_with, description, fractional_qty_value)
        except asyncpg.exceptions.NotNullViolationError as exc:
            raise AccountError(
                f'Has no registered account with id: {user_id}',
            ) from exc


async def _debiting_balance(
        user_id: int,
        qty_value: Decimal,
        db_con: Connection,
        deal_with: Optional[int] = None,
        description: Optional[str] = None,
) -> None:
    deal_with = user_id if deal_with is None else deal_with
    description = 'withdraw' if description is None else description
    fractional_qty_value = int(qty_value * FRACTIONAL_VALUE)
    query = """ INSERT INTO transactions (
                    account_id, deal_with, description, qty_change
                )
                VALUES (
                    (SELECT id FROM accounts WHERE user_id = $1), $2, $3, $4
                );"""
    if not await _has_account(user_id, db_con):
        raise AccountError(f'Has no registered account with id: {user_id}')
    async with db_con.transaction():
        balance = await _compute_balance(user_id, db_con)
        if balance - abs(fractional_qty_value) >= 0:
            # Make quantity value negative
            await db_con.execute(query, user_id, deal_with, description, -fractional_qty_value)
        else:
            raise BalanceValueError(
                f'Insufficient funds on the account: {user_id}',
            )


async def _fetch_currency_rate(cur_name: str, db_con: Connection) -> Decimal:
    query = """ SELECT rate_to_base FROM currencies WHERE cur_name = $1;"""
    rate = await db_con.fetchval(query, cur_name)
    if rate is None:
        raise CurrencyError(f'Unsupported currency type: {cur_name}')
    else:
        return Decimal(rate)


async def _compute_balance(user_id: int, db_con: Connection) -> Decimal:
    balance_query = """ SELECT sum(qty_change)
                        FROM transactions
                        WHERE account_id = (
                            SELECT id FROM accounts WHERE user_id = $1
                        );"""
    balance = await db_con.fetchval(balance_query, user_id)
    return Decimal(0) if balance is None else Decimal(balance)


async def _get_sort_keys(order_by: Union[str, List[str]]):
    sort_keys = ['', '']
    for key, val in enumerate(order_by):
        column_name = val[1:] if val[0] == '-' else val
        order = 'DESC' if val[0] == '-' else 'ASC'
        sort_keys[key] = f'{column_name} {order}'
    coma = ',' if sort_keys[1] else ''
    return sort_keys[0], sort_keys[1], coma


async def _has_account(user_id: int, db_con: Connection):
    query = """ SELECT user_id FROM accounts WHERE user_id = $1;"""
    return user_id == await db_con.fetchval(query, user_id)
