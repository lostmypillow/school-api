from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import InterfaceError
from sqlalchemy import text, URL
import pathlib
from os import getenv, path
import pyodbc
from typing import Literal
from config import settings
pyodbc.pooling = False


# Database connection URL
connection_url = URL.create(
    "mssql+aioodbc",
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    database=settings.DB_NAME,
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
    expire_on_commit=False,
)


async def exec_sql(
        mode: Literal['commit', 'one', 'all'],
        command_name: str,
        **kwargs
):
    """executes SQL statement based on file name

    Parameters
    ----------
    mode : Literal[&#39;commit&#39;, &#39;one&#39;, &#39;all&#39;]
        mode of SQL operation, 'commit' for UPDATE and INSERT, 'one' or 'all' for SELECT

    command_name : str
        name of sql file

    Returns
    -------
    Any
        I say Any cuz it might return dict, None or list, or not return anything at all
    """

    # Gets file path of the .sql file
    # File path shoud be should be (root)/database/sql/xxx.sql
    file_path = path.join(
        pathlib.Path(__file__).parent.resolve(),
        'sql',
        command_name + '.sql'
    )

    print(kwargs)


    # Reads the SQL statement from file
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        sql_command = file_buffer.read()

    # Creates an async session using the async sessionmaker
    async with create_session() as session:

        # Executes the statement
        result = await session.execute(text(sql_command), kwargs)

        if mode == "commit":

            # Just commit if we don't need a return value
            await session.commit()

        elif mode == "one":

            # Get one result
            one_result = result.fetchone()

            # Return the result as dictionary if result isn't None
            # Otherwise, just return None
            return dict(one_result._mapping) if one_result is not None else {}
        
        elif mode == "all":
            # Returns the results as a list of dicts, or an empty list
            return [dict(row._mapping) for row in result.fetchall()]
