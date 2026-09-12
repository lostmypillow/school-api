import os
from pathlib import Path

from arq.connections import RedisSettings

from app.db.initialize import DB
from app.workers.http_client import close_scrape_client
from app.workers.tasks.bootstrap_sqlite import bootstrap_sqlite
from sqlalchemy import text
from dotenv import load_dotenv
from app.workers.tasks.bootstrap_mssql import bootstrap_mssql
from app.workers.http_client import get_scrape_client

load_dotenv()
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


async def startup(ctx: dict):
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
    print((f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.db'}"))
    ctx["db"] = DB(f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.db'}")
    ctx["mssql_db"] = DB(os.getenv("DB_URL", ""))
    ctx["client"] = get_scrape_client()
    print("ARQ Worker initialized database engine.")


async def shutdown(ctx: dict):
    await close_scrape_client()
    if ctx["db"]:
        await ctx["db"].close()
        print("SQLite database engine disposed.")
    if ctx["mssql_db"]:
        await ctx["mssql_db"].close()
        print("MSSQL database engine disposed.")


class WorkerSettings:
    functions = [bootstrap_sqlite, bootstrap_mssql]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    max_jobs = 10
    job_timeout = 3000
    on_startup = startup
    on_shutdown = shutdown
