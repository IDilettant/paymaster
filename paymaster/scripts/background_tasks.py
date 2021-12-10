import asyncio
import functools
import logging
import os
import threading
import time
from datetime import timedelta, datetime
from typing import Any, Callable, Coroutine, Optional

import freezegun as freezegun
import schedule
from asyncpg import Pool, create_pool
from dotenv import load_dotenv
from paymaster.currencies import get_currencies_rates
from paymaster.database.db import update_currencies
from paymaster.exceptions import CurrencyError

LOGGER = logging.getLogger('schedule')
LOGGER.setLevel(level=logging.DEBUG)


def run_continuously(interval=1):
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


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


async def update_data_currencies(pool: Pool, api_key: Optional[str]):  # noqa: D103 E501
    cur_rates = await get_currencies_rates(api_key)
    async with pool.acquire() as db_conn:
        await update_currencies(cur_rates, db_conn)


async def run_background_job() -> None:
    load_dotenv()
    dsn: Optional[str] = os.getenv('DSN')
    api_key: Optional[str] = os.getenv('API_KEY')
    pool = await create_pool(dsn)
    await update_data_currencies(pool, api_key)
    print('Done')


@catch_exceptions(cancel_on_failure=True)
def set_task(task, trigger_time: str):
    schedule.every().day.at(trigger_time).do(
        asyncio.run,
        task(),
    )
    run_continuously()


if __name__ == '__main__':
    now = datetime(2020, 1, 1, 10, 31)
    with freezegun.freeze_time(now) as frozen_date:
        set_task(run_background_job, '10:30')
        frozen_date.move_to(now + timedelta(days=1))
        time.sleep(5)
        print('Now')
