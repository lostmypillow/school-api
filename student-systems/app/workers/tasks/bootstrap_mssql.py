from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.models import Base
from tqdm.asyncio import tqdm


async def bootstrap_mssql(ctx: dict):
    sqlite_engine: AsyncEngine = ctx["db"].engine
    mssql_engine: AsyncEngine = ctx["mssql_db"].engine

    from sqlalchemy import select

    async with mssql_engine.begin() as ms_conn:
        await ms_conn.run_sync(Base.metadata.create_all)

    # 2. Transfer data table by table in dependency order
    async with sqlite_engine.connect() as sq_conn, mssql_engine.begin() as ms_conn:
        for table in tqdm(Base.metadata.sorted_tables, desc="Migrating tables"):
            # 1. Identify primary key columns
            pk_columns = [col for col in table.primary_key.columns]
            pk_names = [col.name for col in pk_columns]

            # 2. Fetch existing primary keys from MSSQL to avoid duplicates
            existing_pks = set()
            if pk_columns:
                ms_result = await ms_conn.execute(select(*pk_columns))
                # Store existing keys as tuples to support composite primary keys
                existing_pks = {
                    tuple(row[name] for name in pk_names)
                    for row in ms_result.mappings().all()
                }

            # 3. Fetch all rows from SQLite
            result = await sq_conn.execute(table.select())
            rows = result.mappings().all()

            data: list[dict[str, Any]] = []
            for row in rows:
                # 4. Filter out rows that already exist in MSSQL
                # If the table has no primary key, it skips the check and appends everything
                row_pk = tuple(row[name] for name in pk_names) if pk_names else None

                if not pk_names or row_pk not in existing_pks:
                    data.append({str(k): v for k, v in row.items()})

            # 5. Insert only the new rows
            if data:
                await ms_conn.execute(table.insert(), data)
