from asyncpg import Connection, Pool
from fastapi import Depends, Request


def get_db_pool(request: Request) -> Pool:
    return request.app.state.pool


async def get_connection_from_pool(
    pool: Pool = Depends(get_db_pool),
) -> Connection:
    async with pool.acquire() as conn:
        yield conn
