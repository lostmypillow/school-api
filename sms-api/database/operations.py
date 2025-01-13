from sqlalchemy import create_engine, text
import pathlib
import os
from dotenv import load_dotenv

load_dotenv()

connection_url = 
engine = create_engine(connection_url)


def sql_from_file(command_name):
    file_path = os.path.join(pathlib.Path(
        __file__).parent.resolve(), 'sql',  command_name + '.sql')
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        return file_buffer.read()


def commit_sql(command_name, **kwargs):
    with engine.connect() as conn:
        conn.execute(text(sql_from_file(command_name)), kwargs)
        conn.commit()


def fetch_one_sql(command_name, **kwargs):
    with engine.connect() as conn:
        result = conn.execute(text(sql_from_file(command_name)), kwargs)
        return result.fetchone()


def fetch_all_sql(command_name, **kwargs):
    with engine.connect() as conn:
        result = conn.execute(text(sql_from_file(command_name)), kwargs)
        return result.fetchall()
