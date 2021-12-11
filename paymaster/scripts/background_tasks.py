"""Background tasks module."""
import asyncio
import functools
import logging
import os
import time
from typing import Any, Callable, Optional

import schedule
from asyncpg import Connection, connect
from dotenv import load_dotenv
from paymaster.currencies import get_currencies_rates
from paymaster.database.db import update_currencies
from paymaster.exceptions import CurrencyError

LOGGER = logging.getLogger('schedule')
LOGGER.setLevel(level=logging.DEBUG)

load_dotenv()

API_KEY: Optional[str] = os.getenv('API_KEY')
DSN: Optional[str] = os.getenv('DSN')


def catch_exceptions(  # noqa: WPS234
    cancel_on_failure: bool = False,
) -> Callable[[Callable[[Callable[[Any, Any], None]], Any]], Any]:  # noqa: WPS221 E501
    """Make decorator for cathing exceptions in background scheduler.

    Args:
        cancel_on_failure: flag of finishing on failure scheduler work

    Returns:
        catch exceptions decorator
    """
    def catch_exceptions_decorator(  # noqa: WPS430
        job_func: Callable[[Callable[[Any, Any], None]], Any],  # noqa: WPS221 E501
    ):
        @functools.wraps(job_func)
        def wrapper(*args):
            try:
                return job_func(*args)
            except (CurrencyError, RuntimeError) as exc:
                LOGGER.warning(exc)
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator


async def update_currency_rates_job(db_conn: Connection) -> None:  # noqa: D103 E501
    cur_rates = await get_currencies_rates(API_KEY)
    await update_currencies(cur_rates, db_conn)


async def _run_background_job() -> None:
    db_conn = await connect(DSN)
    await update_currency_rates_job(db_conn)


@catch_exceptions(cancel_on_failure=True)  # type: ignore
def _set_task(
    task,
    trigger_time,
) -> None:
    schedule.every().day.at(trigger_time).do(
        asyncio.run,
        task(),
    )
    while True:  # noqa: WPS457
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    asyncio.run(_run_background_job())
    _set_task(_run_background_job, '18:11')
