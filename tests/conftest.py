"""Fixtures module."""
import os
from typing import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer


@pytest.fixture
async def dsn() -> str:
    with PostgresContainer("postgres:12-alpine") as postgres:
        # FastAPI expects a link of the form "postgresql://test:test@localhost:<port>/test" to connect to database
        # Testcontainers-supplied link "postgresql+psycopg2://test:test@localhost:<port>/test"
        # contains an extra part: "+psycopg2". Which needs to get rid of for testing purposes
        yield postgres.get_connection_url().replace('+psycopg2', '')


@pytest.fixture
def non_mocked_hosts() -> list:
    return ['testserver']


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    # local import for testing purpose
    from paymaster.scripts.main import get_application

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
