from django.db import connection

def execute_sql(sql: str, params: list = None) -> list:
    """
    Executes a raw SQL query and returns results as a list of dictionaries.
    """
    if params is None:
        params = []
        
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        
        # If the statement doesn't return rows (INSERT/UPDATE), cursor.description is None
        if cursor.description is None:
            return [{"message": "Operation executed successfully"}]

        # Fetch column names from cursor description
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

