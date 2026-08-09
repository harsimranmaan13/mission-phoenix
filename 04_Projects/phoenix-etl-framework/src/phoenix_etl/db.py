import os

import psycopg


def get_connection() -> psycopg.Connection:
    """Create a PostgreSQL connection for the Phoenix ETL database."""

    connection = psycopg.connect(
        host=os.getenv("PHOENIX_DB_HOST", "localhost"),
        port=int(os.getenv("PHOENIX_DB_PORT", "5432")),
        dbname=os.getenv("PHOENIX_DB_NAME", "phoenix_etl"),
        user=os.getenv("PHOENIX_DB_USER", "postgres"),
        password=os.getenv("PHOENIX_DB_PASSWORD"),
    )

    connection.execute("SET search_path TO phoenix")

    return connection
