"""Ejemplo de uso

from .sql import QueryManager
import os

sql_dir = os.path.join(os.path.dirname(__file__), 'sql_files')

qm = QueryManager(sql_dir)
select_query = qm.fetch_data
insert_query = qm.insert_data
update_query = qm.update_data
delete_query = qm.delete_data

"""

import os

class QueryManager:
    """Clase para manejar queries SQL

    Returns:
        - QueryManager
    
    Uso:
        - qm = QueryManager(sql_dir)
        - select_query = qm.fetch_data
    """
    sql_dir = None
    sql_files = None

    def __init__(self, sql_dir):
        self.sql_dir = sql_dir
        # - Find all .sql files for the given directory and put them in a list
        self.sql_files = [
            f for f in os.listdir(self.sql_dir) if os.path.isfile(os.path.join(self.sql_dir, f)) and '.sql' in f
        ]

    def __getattr__(self, item) -> str:
        """
           Lets query file be fetched by calling the query manager class object with the name of the query as the attribute
        """

        if item + '.sql' in self.sql_files:
            # - This is where the file is actually read
            with open(os.path.join(self.sql_dir, item + '.sql'), 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise AttributeError(f'QueryManager no encontro el archivo {str(item)}.sql')
