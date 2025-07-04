import importlib
import sys
import types


def load_connection(monkeypatch):
    """Load ``src.db.connection`` using an in-memory SQLite engine."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DB_USERNAME", "x")
    monkeypatch.setenv("DB_PASSWORD", "x")
    monkeypatch.setenv("DB_SERVER", "x")
    monkeypatch.setenv("DB_DATABASE", "x")

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "dotenv", dotenv)

    engine = importlib.reload(importlib.import_module("src.db.engine"))
    from sqlalchemy import create_engine as sa_create_engine
    from sqlalchemy.orm import sessionmaker

    engine.engine = sa_create_engine("sqlite:///:memory:")
    engine.SessionLocal = sessionmaker(
        bind=engine.engine, autocommit=False, autoflush=False
    )

    importlib.reload(importlib.import_module("src.db.session"))
    module = importlib.reload(importlib.import_module("src.db.connection"))
    return module


def test_connection_success(monkeypatch):
    db = load_connection(monkeypatch)
    assert db.test_connection() is True


def test_execute_query(monkeypatch):
    db = load_connection(monkeypatch)
    result = db.execute_query("SELECT 1 AS value")
    assert result == [{"value": 1}]


def test_execute_query_with_params(monkeypatch):
    db = load_connection(monkeypatch)

    class DummyResult:
        def keys(self):
            return ["total"]

        def fetchall(self):
            return [(3,)]

    class DummySession:
        def execute(self, query, params):
            assert params == {"a": 1, "b": 2}
            return DummyResult()

        def commit(self):
            pass

    from contextlib import contextmanager

    @contextmanager
    def dummy_get_session():
        yield DummySession()

    monkeypatch.setattr(db, "get_session", dummy_get_session)

    result = db.execute_query("SELECT :a + :b AS total", {"a": 1, "b": 2})
    assert result == [{"total": 3}]
