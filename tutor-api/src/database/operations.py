from sqlalchemy import create_engine, text
import pathlib
import os
from dotenv import load_dotenv

load_dotenv()

connection_url: str = f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_URL')}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(connection_url)


def sql_from_file(command_name: str) -> str:
    """Reads and extracts SQL string from .sql files

    Parameters
    ----------
    command_name : str
        SQL file name. MUST match .sql file name.

    Returns
    -------
    str
        SQL string from sql file
    """

    # This gets the .sql file from the sql folder at the same root as operations.py
    file_path = os.path.join(pathlib.Path(
        __file__).parent.resolve(), 'sql',  command_name + '.sql')

    # Returns the extracted string from the .sql file
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        return file_buffer.read()


# This entire operations.py file is actually adapted from the same operations.py in  http://192.168.2.7:3000/lostmypillow/KwExamID/src/branch/main/database. 

# Except the separate commit_sql, fetch_one_sql...functions became one single execute_SQL function here simply because execute_SQL was written this way in this project since the beginning. 

# It is therefore safe to adapt the same functions from KwExamID if you wish to. For now, if it ain't broke I ain't fixing it.
def execute_SQL(command_name: str, **kwargs):
    """executes SQL from a given command name

    Parameters
    ----------
    command_name : str
        filename of the .sql file to execute
    """

    # using the "with...as..." syntax, we ensure the engine connection terminates at the end of the function
    with engine.connect() as conn:

        # Gets the result
        result = conn.execute(text(sql_from_file(command_name)), kwargs)

        # If it's a commit based operations, aka INSERT, UPDATE, CREATE TABLE IF NOT EXISTS...
        if command_name in [
            "register_insert",
            "register_update_student", "register_update_teacher", "check_device_db"
        ]:
            conn.commit()

        # If it's just SELECT...
        else:

            return result.fetchone()
