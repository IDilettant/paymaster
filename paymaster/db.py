"""Database module."""
import asyncio
from typing import Optional, Tuple, List

import asyncpg
from asyncpg import Connection

FRACTIONAL_VALUE = 100


async def create_acc(user_id: int, db_con: Connection) -> None:
    query = """INSERT INTO accounts (user_id) VALUES ($1);"""
    await db_con.execute(query, user_id)


async def delete_acc(user_id: int, db_con: Connection) -> None:
    op_query = """  DELETE FROM transactions
                    WHERE account_id = (
                        SELECT id FROM accounts
                        WHERE user_id = $1
                    );"""
    acc_query = """ DELETE FROM accounts
                    WHERE user_id = ($1);"""
    async with db_con.transaction():
        await db_con.execute(op_query, user_id)
        await db_con.execute(acc_query, user_id)


async def crediting_funds(
        user_id: int, 
        qty_value: int, 
        db_con: Connection,
        deal_with: Optional[int] = None,
        description: str = 'balance replenishment',
) -> None:
    deal_with = user_id if deal_with is None else deal_with
    fractional_qty_value = qty_value * FRACTIONAL_VALUE
    query = """ INSERT INTO transactions (account_id, deal_with, description, qty_change)
                VALUES ((SELECT id FROM accounts WHERE user_id = $1), $2, $3, $4);"""
    # What if acc isn't exist yet? 
    # asyncpg.exceptions.NotNullViolationError: null value in column "account_id" violates not-null constraint
    # what privacy level need?
    async with db_con.transaction():
        await db_con.execute(query, user_id, deal_with, description, fractional_qty_value)  # TODO: write the exception


async def debiting_funds(
        user_id: int, 
        qty_value: int, 
        db_con: Connection, 
        deal_with: Optional[int] = None, 
        description: str = 'funds withdrawal',
) -> None:
    deal_with = user_id if deal_with is None else deal_with
    fractional_qty_value = qty_value * FRACTIONAL_VALUE
    query = """ INSERT INTO transactions (
                    account_id, deal_with, description, qty_change
                )
                VALUES (
                    (SELECT id FROM accounts WHERE user_id = $1), $2, $3, $4
                );"""
    #  Check balance before debiting and rise exception
    async with db_con.transaction():
        balance = await _compute_balance(user_id, db_con)
        if balance - fractional_qty_value >= 0:
            await db_con.execute(query, user_id, deal_with, description, -fractional_qty_value)  # Make quantity value negative
        else:
            raise Exception  # TODO: write the exception


async def send_between_users(
        sender_id: int, 
        recipient_id: int, 
        qty_value: int, 
        db_con: Connection, 
        transaction_aim: str = 'payment',  # Is username needed?
) -> None:
    async with db_con.transaction():
        # description = f'Paying to {recipient_id} for {transaction_aim}'
        await debiting_funds(
            user_id=sender_id, 
            deal_with=recipient_id, 
            qty_value=qty_value, 
            description=transaction_aim, 
            db_con=db_con,
        )
        # description = f'Getting payment from {sender_id} for {transaction_aim}'
        await crediting_funds(
            user_id=recipient_id,
            deal_with=sender_id,
            qty_value=qty_value,
            description=transaction_aim,
            db_con=db_con,
        )


async def get_balance(user_id: int, db_con: Connection, convert_to: str = '') -> float:
    rate_query = """SELECT rate_to_base
                    FROM currencies
                    WHERE currencies.cur_name = $1;"""
    balance = await _compute_balance(user_id, db_con) / FRACTIONAL_VALUE  # TODO: exception for no acc
    cur_rate = await db_con.fetchval(rate_query, convert_to) if convert_to else 1  # TODO: exception for no currency
    return round(balance * cur_rate, 2)  # Should I convert here or in app?


async def fetch_acc_history(user_id: int, db_con: Connection) -> Tuple[dict]:
    query = """ SELECT created_at, deal_with, description, qty_change
                FROM transactions 
                WHERE account_id = (
                    SELECT id FROM accounts WHERE user_id = $1
                );"""
    return tuple(map(dict, await db_con.fetch(query, user_id)))


async def fetch_currency_rate(cur_name: str, db_con: Connection) -> float:
    query = """ SELECT rate_to_base 
                FROM currencies 
                WHERE cur_name = $1;"""
    return await db_con.fetchval(query, cur_name)


async def update_currencies(cur_rates: List[Tuple], db_con: Connection) -> None:
    query = """ INSERT INTO currencies (cur_name, rate_to_base)
                VALUES ($1, $2)
                ON CONFLICT (cur_name)
                DO UPDATE SET rate_to_base = $2
                WHERE currencies.cur_name = $1;"""
    await db_con.executemany(query, cur_rates)


async def _compute_balance(user_id: int, db_con: Connection) -> int:  # TODO: exception for no acc or transactions
    balance_query = """ SELECT sum(qty_change)
                    FROM transactions
                    WHERE account_id = (
                        SELECT id FROM accounts WHERE user_id = $1
                    );"""
    return await db_con.fetchval(balance_query, user_id)
