"""Database dependencies for app."""
from asyncpg import Connection, Pool
from fastapi import Depends, Request


def get_db_pool(request: Request) -> Pool:
    """Extract database connections pool from app.

    Args:
        request: request containing application instance

    Returns:
        database connections pool
    """
    return request.app.state.pool


async def get_connection_from_pool(
    pool: Pool = Depends(get_db_pool),  # noqa: WPS404
) -> Connection:
    """Get connection from database connections pool.

    Args:
        pool: database connections pool

    Yields:
        database connection
    """
    async with pool.acquire() as conn:
        yield conn
