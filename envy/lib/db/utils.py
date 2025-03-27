import sqlite3
import os
import envy


def get_server_ip() -> str:
    path = os.path.join(os.path.dirname(envy.__file__), 'Jobs')
    database = 'Envy_Database.db'
    database_path = os.path.join(path, database)
    con = sqlite3.connect(f'file:{database_path}?mode=ro', uri=True, timeout=5)
    cursor = con.cursor()
    query = "SELECT server FROM server"
    cursor.execute(query)
    result = cursor.fetchone()[0]

    return result
