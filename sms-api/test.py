import pyodbc

connection_string = 'Driver={ODBC Driver 18 for SQL Server};Server=your_server;Database=your_db;Encrypt=yes;TrustServerCertificate=yes;'

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()
cursor.execute('SELECT @@VERSION')
row = cursor.fetchone()
print(row)
