import pyodbc
from config import settings
connection_string = (
    f'Driver={{ODBC Driver 18 for SQL Server}};'
    f'Server={settings.DB_HOST};'
    f'Database={settings.DB_NAME};'
    f'UID={settings.DB_USERNAME};'
    f'PWD={settings.DB_PASSWORD};'
    f'TrustServerCertificate=yes;'
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()
cursor.execute('SELECT @@VERSION')
row = cursor.fetchone()
print(row)
