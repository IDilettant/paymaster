from datetime import datetime
from asyncpg import Connection

import pytest

from paymaster.app import API_KEY
from paymaster.currencies import get_currencies_rates
from paymaster.db import (
    create_acc,
    delete_acc,
    crediting_funds,
    debiting_funds,
    send_between_users,
    get_balance,
    fetch_acc_history,
    fetch_currency_rate,
    update_currencies, FRACTIONAL_VALUE,
)

pytestmark = pytest.mark.asyncio  # All test coroutines will be treated as marked.
USER_ID = 73


async def test_db_exists(db_conn: Connection, db_name: str = 'treasury'):
    query = """ SELECT datname FROM pg_database 
                WHERE datname = $1;"""
    resp = await db_conn.fetchval(query, db_name)
    assert resp == db_name


@pytest.mark.parametrize(
    'table_name',
    [
        'accounts',
        'transactions',
        'currencies',
    ],
)
async def test_tables_exists(table_name: str, db_conn: Connection):
    query = """ SELECT table_name FROM information_schema.tables 
                WHERE table_name = $1;"""
    resp = await db_conn.fetchval(query, table_name)
    assert resp == table_name


async def test_create_acc(db_conn: Connection):
    query = """SELECT user_id FROM accounts WHERE user_id = $1;"""
    await create_acc(USER_ID, db_conn)
    resp = await db_conn.fetchval(query, USER_ID)
    assert resp == USER_ID


async def test_delete_acc(db_conn: Connection):
    query = """SELECT user_id FROM accounts WHERE user_id = $1;"""
    await create_acc(USER_ID, db_conn)
    await delete_acc(USER_ID, db_conn)
    resp = await db_conn.fetchval(query, USER_ID)
    assert resp is None


async def test_crediting_funds(db_conn: Connection):
    qty_value = 333
    await create_acc(USER_ID, db_conn)
    await crediting_funds(USER_ID, qty_value, db_conn)
    balance = await get_balance(USER_ID, db_conn)
    assert balance == qty_value


async def test_debiting_funds(db_conn: Connection):
    qty_value = 333
    await create_acc(USER_ID, db_conn)
    await crediting_funds(USER_ID, qty_value * 2, db_conn)
    await debiting_funds(USER_ID, qty_value, db_conn)
    balance = await get_balance(USER_ID, db_conn)
    assert balance == qty_value


async def test_send_between_users(db_conn: Connection):
    qty_value = 333
    send_amount = 42
    recipient_user_id = 123
    await create_acc(USER_ID, db_conn)
    await create_acc(recipient_user_id, db_conn)
    await crediting_funds(USER_ID, qty_value, db_conn)
    await send_between_users(USER_ID, recipient_user_id, send_amount, db_conn)
    sender_balance = await get_balance(USER_ID, db_conn)
    recipient_balance = await get_balance(recipient_user_id, db_conn)
    assert sender_balance == qty_value - send_amount
    assert recipient_balance == send_amount


async def test_fetch_acc_history(db_conn: Connection):
    qty_value = 333
    await create_acc(USER_ID, db_conn)
    await crediting_funds(USER_ID, qty_value, db_conn)
    await debiting_funds(USER_ID, qty_value, db_conn)
    history = await fetch_acc_history(USER_ID, db_conn)
    assert isinstance(history, tuple)
    assert all(map(lambda record: isinstance(record, dict), history))
    assert len(history) == 2
    assert history[0]['deal_with'] == USER_ID
    assert history[0]['qty_change'] == qty_value * FRACTIONAL_VALUE
    assert history[1]['qty_change'] == -qty_value * FRACTIONAL_VALUE


async def test_update_currencies(db_conn: Connection):
    query = """SELECT updated_at FROM currencies LIMIT 1;"""
    cur_rates = await get_currencies_rates(API_KEY)
    await update_currencies(cur_rates, db_conn)
    date = await db_conn.fetchval(query)
    assert date.date() == datetime.now().date()


async def test_fetch_currency_rate(db_conn: Connection):
    cur_rates = await get_currencies_rates(API_KEY)
    await update_currencies(cur_rates, db_conn)
    cur_rate = await fetch_currency_rate('RUB', db_conn)
    assert cur_rate == 1
