"""Migrations and up/shutdown handlers."""
import os
import pathlib
from typing import Any, Callable, Coroutine, Optional

from asyncpg import create_pool
from fastapi import FastAPI
from paymaster.scripts.background_tasks import update_data_currencies
from yoyo import get_backend, read_migrations


def make_migration(dsn: str) -> None:
    """Make migrations from sql directory.

    Args:
        dsn: database url
    """
    file_path = str(
        pathlib.Path(__file__).parent / '..' / '..' / 'sql',
    )
    backend = get_backend(dsn)
    migrations = read_migrations(file_path)
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def create_start_app_handler(
    app: FastAPI,
) -> Callable[[], Coroutine[Any, Any, None]]:
    """Create handler for pre-started app preparing.

    Args:
        app: app instance

    Returns:
        started handler
    """
    async def start_app() -> None:  # noqa: WPS430
        dsn: Optional[str] = os.getenv('DSN')
        api_key: Optional[str] = os.getenv('API_KEY')
        app.state.pool = await create_pool(dsn)
        if dsn is not None:
            make_migration(dsn)
        await update_data_currencies(app.state.pool, api_key)
    return start_app


def create_stop_app_handler(
    app: FastAPI,
) -> Callable[[], Coroutine[Any, Any, None]]:
    """Create handler for pre-shutdown app preparing.

    Args:
        app: app instance

    Returns:
        shutdown handler
    """
    async def stop_app() -> None:  # noqa: WPS430
        await app.state.pool.close()
    return stop_app
