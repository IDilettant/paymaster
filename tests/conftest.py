"""Fixtures module."""
import os

import pytest
from asgi_lifespan import LifespanManager
from asyncpg import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer


@pytest.fixture
async def dsn() -> Pool:
    with PostgresContainer("postgres:12") as postgres:
        yield postgres.get_connection_url().replace('+psycopg2', '')  # Delete from dsn url unnecessary path part


@pytest.fixture
async def app() -> FastAPI:
    from paymaster.main import \
        get_application  # local import for testing purpose

    yield get_application()


@pytest.fixture
async def initialized_app(app: FastAPI, dsn: str) -> FastAPI:
    os.environ['DSN'] = dsn
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(initialized_app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        app=initialized_app,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
async def db_conn(initialized_app):
    async with initialized_app.state.pool as pool:
        async with pool.acquire() as conn:
            yield conn
