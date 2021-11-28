import os
import pathlib
from typing import Callable

import asyncpg
from fastapi import FastAPI
from yoyo import get_backend, read_migrations


def make_migration(dsn: str):
    file_path = str(pathlib.Path('__file__').parent / '..' / 'sql')
    backend = get_backend(dsn)
    migrations = read_migrations(file_path)
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        dsn = os.getenv('DSN')
        app.state.pool = await asyncpg.create_pool(dsn)
        make_migration(dsn)
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        await app.state.pool.close()
    return stop_app
