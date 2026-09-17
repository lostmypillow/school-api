import logging
import os
from pathlib import Path

import httpx
from arq.connections import RedisSettings

from app.core.custom_http_client import CustomAsyncClient
from app.core.initialize import DB
from app.domains.courses.bootstrap_sqlite import bootstrap_sqlite
from sqlalchemy import text
from dotenv import load_dotenv
from app.domains.courses.bootstrap_mssql import bootstrap_mssql
load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_client: CustomAsyncClient | None = None

async def startup(ctx: dict):
    print(DATA_DIR)
    bootstrap_engine = DB(os.getenv("BOOTSTRAP_URL", "")).engine

    async with bootstrap_engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        result = await conn.execute(
            text("SELECT name FROM sys.databases WHERE name = 'student_db'")
        )
        db_exists = result.scalar()

        if not db_exists:
            print("Database 'student_db' not found. Creating...")
            await conn.execute(text("CREATE DATABASE student_db"))
            print("Database 'student_db' created successfully.")

    await bootstrap_engine.dispose()
    print((f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_bootstrap.db'}"))
    ctx["database"] = DB(f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_bootstrap.db'}")
    ctx["mssql_db"] = DB(os.getenv("DB_URL", ""))
    limits = httpx.Limits(
            max_connections=10, max_keepalive_connections=10
        )
    ctx["client"] = CustomAsyncClient(
            verify=False, limits=limits, timeout=30.0
        )
    print("ARQ Worker initialized database engine.")


async def shutdown(ctx: dict):
    if ctx["database"]:
        await ctx["database"].close()
        print("SQLite database engine disposed.")
    if ctx["mssql_db"]:
        await ctx["mssql_db"].close()
        print("MSSQL database engine disposed.")
    if ctx["client"] is not None and not ctx["client"].is_closed:
        await ctx["client"].aclose()
        ctx["client"] = None


class WorkerSettings:
    functions = [bootstrap_sqlite, bootstrap_mssql]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    max_jobs = 10
    job_timeout = 3000
    on_startup = startup
    on_shutdown = shutdown


logger = logging.getLogger(__name__)



