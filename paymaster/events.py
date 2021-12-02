"""Migrations and up/shutdown handlers."""
import os
import pathlib
from typing import Callable

import asyncpg
from fastapi import FastAPI
from paymaster.currencies import get_currencies_rates
from paymaster.db import update_currencies
from yoyo import get_backend, read_migrations


def make_migration(dsn: str) -> None:
    """Make migrations from sql directory.

    Args:
        dsn: database url
    """
    file_path = str(pathlib.Path(__file__).parent / '..' / 'sql')
    backend = get_backend(dsn)
    migrations = read_migrations(file_path)
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def create_start_app_handler(app: FastAPI) -> Callable:
    """Create handler for pre-started app preparing.

    Args:
        app: app instance

    Returns:
        started handler
    """
    async def start_app() -> None:  # noqa: WPS430
        dsn = os.getenv('DSN')
        api_key = os.getenv('API_KEY')
        app.state.pool = await asyncpg.create_pool(dsn)
        make_migration(dsn)
        cur_rates = await get_currencies_rates(api_key)
        await update_currencies(cur_rates, app.state.pool)
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """Create handler for pre-shutdown app preparing.

    Args:
        app: app instance

    Returns:
        shutdown handler
    """
    async def stop_app() -> None:  # noqa: WPS430
        await app.state.pool.close()
    return stop_app
