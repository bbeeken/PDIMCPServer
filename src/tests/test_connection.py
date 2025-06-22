import importlib
import sqlite3
import sys
import types


def load_connection(monkeypatch):
    """Load src.db.connection with a stubbed pyodbc module using SQLite."""
    pyodbc = types.ModuleType("pyodbc")

    class DummyConnection:
        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.autocommit = False

        def cursor(self):
            return self.conn.cursor()

        def close(self):
            self.conn.close()

        def commit(self):
            self.conn.commit()

    pyodbc.connect = lambda *_args, **_kw: DummyConnection()
    pyodbc.paramstyle = "qmark"
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None

    monkeypatch.setitem(sys.modules, "pyodbc", pyodbc)
    monkeypatch.setitem(sys.modules, "dotenv", dotenv)

    module = importlib.reload(importlib.import_module("src.db.connection"))
    module._connection_pool.clear()
    return module


def test_connection_success(monkeypatch):
    db = load_connection(monkeypatch)
    assert db.test_connection() is True


def test_execute_query(monkeypatch):
    db = load_connection(monkeypatch)
    result = db.execute_query("SELECT 1 AS value")
    assert result == [{"value": 1}]
