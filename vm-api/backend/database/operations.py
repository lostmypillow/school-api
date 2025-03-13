from sqlalchemy import create_engine, text
import pathlib
import os
from dotenv import load_dotenv

connection_url: str = f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_URL')}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(connection_url)


def sql_from_file(command_name):
    """Reads and extracts SQL string from .sql files

    Parameters
    ----------
    command_name : str
        filename of the .sql file to execute

    Returns
    -------
    str
        SQL string from sql file
    """
    file_path = os.path.join(pathlib.Path(
        __file__).parent.resolve(), 'sql',  command_name + '.sql')
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        return file_buffer.read()


def commit_sql(command_name, **kwargs):
    """Executes INSERT, UPDATE...commands

    Parameters
    ----------
    command_name : str
        filename of the .sql file to execute
    """
    with engine.connect() as conn:
        conn.execute(text(sql_from_file(command_name)), kwargs)
        conn.commit()


def fetch_one_sql(command_name, **kwargs):
    """Gets ONE result from SELECT query

    Parameters
    ----------
    command_name : str
        filename of the .sql file to execute

    Returns
    -------
    Optional
        IDK, that's what SQLAlchemy returns
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql_from_file(command_name)), kwargs)
        return result.fetchone()
    
def fetch_all_sql(command_name, **kwargs):
    """Gets ALL results from SELECT query

    Parameters
    ----------
    command_name : str
        filename of the .sql file to execute

    Returns
    -------
    Optional
        IDK, that's what SQLAlchemy returns
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql_from_file(command_name)), kwargs)
        return result.fetchall()
