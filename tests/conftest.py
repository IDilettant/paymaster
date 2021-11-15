"""Fixtures module."""
import asyncpg
import pytest

DSN = 'postgresql://postgres:postgres@localhost:5432'


@pytest.fixture()
async def db_conn():
    connection = await asyncpg.connect(dsn=DSN)
    transaction = connection.transaction()
    await transaction.start()
    yield connection
    await transaction.rollback()
    await connection.close()
