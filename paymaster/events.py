"""Migrations and up/shutdown handlers."""
import asyncio
import functools
import logging
import os
import pathlib
from typing import Any, Callable, Coroutine, Optional

import schedule
from asyncpg import Pool, create_pool
from fastapi import BackgroundTasks, FastAPI
from paymaster.currencies import get_currencies_rates
from paymaster.database.db import update_currencies
from paymaster.exceptions import CurrencyError
from yoyo import get_backend, read_migrations

LOGGER = logging.getLogger('schedule')
LOGGER.setLevel(level=logging.DEBUG)


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
        background_tasks = BackgroundTasks()
        dsn: Optional[str] = os.getenv('DSN')
        api_key: Optional[str] = os.getenv('API_KEY')
        app.state.pool = await create_pool(dsn)
        if dsn is not None:
            make_migration(dsn)
        await _update_data_currencies(app.state.pool, api_key)
        background_tasks.add_task(
            _make_currencies_update_regular,
            app.state.pool,
            api_key,
        )
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


def catch_exceptions(  # noqa: WPS234
    cancel_on_failure: bool = False,
) -> Callable[[Callable[[Any, Optional[str]], Coroutine[Any, Any, Any]]], Any]:  # noqa: WPS221 E501
    """Make decorator for cathing exceptions in background scheduler.

    Args:
        cancel_on_failure: flag of finishing on failure scheduler work

    Returns:
        catch exceptions decorator
    """
    def catch_exceptions_decorator(  # noqa: WPS430
        job_func: Callable[[Any, Optional[str]], Coroutine[Any, Any, Any]],  # noqa: WPS221 E501
    ):
        @functools.wraps(job_func)
        def wrapper(*args):
            try:
                return job_func(*args)
            except CurrencyError as exc:
                LOGGER.warning(exc)
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


@catch_exceptions(cancel_on_failure=True)
async def _update_data_currencies(pool: Pool, api_key: Optional[str]):
    cur_rates = await get_currencies_rates(api_key)
    await update_currencies(cur_rates, pool)


async def _make_currencies_update_regular(pool: Pool, api_key: Optional[str]):
    schedule.every().day.at('00:00').do(
        _update_data_currencies,
        poll=pool,
        api_key=api_key,
    )
    while True:  # noqa: WPS457
        schedule.run_pending()
        asyncio.sleep(1)
