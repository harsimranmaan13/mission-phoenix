from phoenix_etl.config import load_config


def test_load_config_uses_defaults(monkeypatch) -> None:
    monkeypatch.delenv("PHOENIX_DB_HOST", raising=False)
    monkeypatch.delenv("PHOENIX_DB_PORT", raising=False)
    monkeypatch.delenv("PHOENIX_DB_NAME", raising=False)
    monkeypatch.delenv("PHOENIX_DB_USER", raising=False)
    monkeypatch.delenv("PHOENIX_DB_PASSWORD", raising=False)
    monkeypatch.delenv("PHOENIX_LOG_LEVEL", raising=False)

    config = load_config()

    assert config.database.host == "localhost"
    assert config.database.port == 5432
    assert config.database.name == "phoenix_etl"
    assert config.database.user == "postgres"
    assert config.database.password == ""
    assert config.log_level == "INFO"


def test_load_config_reads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("PHOENIX_DB_HOST", "db-server")
    monkeypatch.setenv("PHOENIX_DB_PORT", "5433")
    monkeypatch.setenv("PHOENIX_DB_NAME", "production_etl")
    monkeypatch.setenv("PHOENIX_DB_USER", "etl_user")
    monkeypatch.setenv("PHOENIX_DB_PASSWORD", "secret")
    monkeypatch.setenv("PHOENIX_LOG_LEVEL", "debug")

    config = load_config()

    assert config.database.host == "db-server"
    assert config.database.port == 5433
    assert config.database.name == "production_etl"
    assert config.database.user == "etl_user"
    assert config.database.password == "secret"
    assert config.log_level == "DEBUG"


def test_config_is_immutable() -> None:
    config = load_config()

    try:
        config.log_level = "DEBUG"
    except AttributeError:
        pass
    else:
        raise AssertionError("AppConfig should be immutable")
