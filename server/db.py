import os
import asyncpg
import asyncio
from typing import Optional
from .config import get_postgres_auth, use_native_postgres_password


class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._refresh_task: Optional[asyncio.Task] = None

    async def get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            token, user = get_postgres_auth()
            host = os.environ["PGHOST"]
            port = int(os.environ.get("PGPORT", "5432"))
            database = os.environ.get("PGDATABASE", "batch_release_db")
            print(f"Connecting to Lakebase: host={host}, port={port}, db={database}, user={user}")
            self._pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=user,
                password=token,
                ssl="require",
                min_size=2,
                max_size=10,
            )
            print("Lakebase connection pool created successfully")
            # Native Postgres passwords are long-lived, so no periodic OAuth refresh is needed.
            if not use_native_postgres_password() and self._refresh_task is None:
                self._refresh_task = asyncio.create_task(self._token_refresh_loop())
        return self._pool

    async def _token_refresh_loop(self):
        """Refresh OAuth token every 45 minutes."""
        while True:
            await asyncio.sleep(45 * 60)
            try:
                if self._pool:
                    await self._pool.close()
                    self._pool = None
                await self.get_pool()
            except Exception as e:
                print(f"Token refresh failed: {e}")

    async def close(self):
        if self._refresh_task:
            self._refresh_task.cancel()
        if self._pool:
            await self._pool.close()


db = DatabasePool()
