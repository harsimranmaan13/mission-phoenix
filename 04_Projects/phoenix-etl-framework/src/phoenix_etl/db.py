import psycopg

from phoenix_etl.config import load_config


def get_connection() -> psycopg.Connection:
    """Create a PostgreSQL connection for the Phoenix ETL database."""

    config = load_config().database

    connection = psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.name,
        user=config.user,
        password=config.password,
    )

    connection.execute("SET search_path TO phoenix")

    return connection
