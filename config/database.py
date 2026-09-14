"""Async PostgreSQL connection pool using asyncpg."""

import asyncpg
from typing import Any, List, Optional
from config.settings import settings

_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.asyncpg_url,
            min_size=2,
            max_size=10,
            command_timeout=30
        )
        print("[Database] Connection pool created.")
    return _pool

async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        print("[Database] Connection pool closed.")

async def query(sql: str, *params) -> List[asyncpg.Record]:
    """
    Execute a SQL query and return all rows.
    Uses $1, $2, ... placeholders (asyncpg native format).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(sql, *params)

async def query_one(sql: str, *params) -> Optional[asyncpg.Record]:
    """Execute a SQL query and return a single row or None."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(sql, *params)

async def execute(sql: str, *params) -> str:
    """Execute a SQL command (INSERT, UPDATE, DELETE) and return status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(sql, *params)

async def check_connection() -> bool:
    """Check if the database is reachable."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        return True
    except Exception:
        return False
