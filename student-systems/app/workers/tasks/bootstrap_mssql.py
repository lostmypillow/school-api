from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.models import Base
from tqdm.asyncio import tqdm
async def bootstrap_mssql(ctx:dict):
    sqlite_engine: AsyncEngine = ctx["db"].engine
    mssql_engine: AsyncEngine = ctx["mssql_db"].engine



    async with mssql_engine.begin() as ms_conn:
        await ms_conn.run_sync(Base.metadata.create_all)

    # 2. Transfer data table by table in dependency order
    async with sqlite_engine.connect() as sq_conn, mssql_engine.begin() as ms_conn:
        for table in tqdm(Base.metadata.sorted_tables, desc="Migrating tables"):
            result = await sq_conn.execute(table.select())
            # mappings() gives a sequence of RowMapping dict-like objects directly
            rows = result.mappings().all()

            if rows:
                data: list[dict[str, Any]] = [
                    {str(k): v for k, v in row.items()} for row in rows
                ]
                await ms_conn.execute(table.insert(), data)

