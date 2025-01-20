from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, URL
import pathlib
from os import getenv, path
from dotenv import load_dotenv
import pyodbc
from typing import Literal

pyodbc.pooling = False

load_dotenv()

# Database connection URL
connection_url = URL.create(
    "mssql+aioodbc",
    username=getenv('DB_USERNAME'),
    password=getenv('DB_PASSWORD'),
    host=getenv('DB_HOST'),
    database=getenv('DB_NAME'),
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "TrustServerCertificate": "yes"
    }
)


# Creating the SQLAlchemy async engine and sessionmaker
async_engine = create_async_engine(
    connection_url,
    pool_size=100,
    max_overflow=0,
    pool_pre_ping=True,
)

# Define an async session maker
create_session = async_sessionmaker(
    async_engine,
    expire_on_commit=False
)


async def sql_from_file(command_name: str) -> str:
    """Returns SQL statement from .sql file

    Parameters
    ----------
    command_name : str
        name of .sql file
    Returns
    -------
    str
        Extracted SQL statement
    """
    file_path = path.join(
        pathlib.Path(__file__).parent.resolve(),
        'sql',
        command_name + '.sql'
    )
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        return file_buffer.read()


async def exec_sql(
        mode: Literal['commit', 'one', 'all'],
        command_name: str,
        **kwargs
):
    async with create_session() as session:
        sql_command = await sql_from_file(command_name)
        result = await session.execute(text(sql_command), kwargs)
        if mode == "commit":
            await session.commit()
        elif mode == "":
            one_result = result.fetchone()
            return one_result._mapping if one_result is not None else one_result
        elif mode == "all":
            all_results = result.mappings().all()
            return all_results