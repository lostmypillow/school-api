from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from typing import Any
import pathlib
import os
from fastapi import Depends
from datetime import date
connection_url = "mssql+aioodbc://testsql:test123456@192.168.2.8/?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
async_engine = create_async_engine(
    connection_url, pool_size=100, max_overflow=0, pool_pre_ping=False)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def sql_from_file(command_name):
    file_path = os.path.join(pathlib.Path(
        __file__).parent.resolve(), 'sql', command_name + '.sql')
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        return file_buffer.read()


async def commit_sql(command_name, **kwargs):
    async with async_session() as session:
        sql_command = await sql_from_file(command_name)
        await session.execute(text(sql_command), kwargs)
        await session.commit()
        await session.close()


async def fetch_one_sql(command_name, **kwargs):
    async with async_session() as session:
        sql_command = await sql_from_file(command_name)
        result = await session.execute(text(sql_command), kwargs)
        one_result = result.fetchone()
        await session.close()
        return one_result


async def fetch_all_sql(command_name, **kwargs):
    async with async_session() as session:
        sql_command = await sql_from_file(command_name)
        result = await session.execute(text(sql_command), kwargs)
        all_results = result.fetchall()
        await session.close()
        return all_results

