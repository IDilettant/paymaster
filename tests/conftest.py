"""Fixtures module."""
import os
from typing import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from asyncpg import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer


@pytest.fixture
async def dsn() -> Pool:
    with PostgresContainer("postgres:12-alpine") as postgres:
        # delete from db url unnecessary path part
        yield postgres.get_connection_url().replace('+psycopg2', '')


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    from paymaster.main import \
        get_application  # local import for testing purpose

    yield get_application()


@pytest.fixture
async def initialized_app(app: FastAPI, dsn: str) -> AsyncIterator[FastAPI]:
    os.environ['DSN'] = dsn
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(initialized_app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        app=initialized_app,
        base_url="http://testserver",
    ) as client:
        yield client
