from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.models import Base
from tqdm.asyncio import tqdm


async def bootstrap_mssql(ctx: dict, *args, **kwargs):
    sqlite_engine: AsyncEngine = ctx["database"].engine
    mssql_engine: AsyncEngine = ctx["mssql_db"].engine

    from sqlalchemy import select

    async with mssql_engine.begin() as ms_conn:
        await ms_conn.run_sync(Base.metadata.create_all)

    # 2. Transfer data table by table in dependency order
    async with sqlite_engine.connect() as sq_conn, mssql_engine.begin() as ms_conn:
        for table in tqdm(Base.metadata.sorted_tables, desc="Migrating tables"):
            pk_columns = [col for col in table.primary_key.columns]

            # 2. Fetch existing primary keys from MSSQL to avoid duplicates
            existing_pks = set()
            if pk_columns:
                ms_result = await ms_conn.execute(select(*pk_columns))
                existing_pks = {tuple(row) for row in ms_result.all()}

                # 3. Stream results from SQLite
                # 3. Stream results from SQLite
                result = await sq_conn.stream(table.select())

                # 4. Chain mappings() BEFORE partitions()
                async for batch in result.mappings().partitions(5000):
                    # Restore the explicit type hint here
                    data: list[dict[str, Any]] = []

                    for row in batch:
                        row_pk = (
                            tuple(row[col.name] for col in pk_columns)
                            if pk_columns
                            else None
                        )

                        if not pk_columns or row_pk not in existing_pks:
                            data.append(dict(row))

                    # 5. Insert the chunk
                    if data:
                        await ms_conn.execute(table.insert(), data)
