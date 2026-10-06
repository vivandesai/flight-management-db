import os
import pytest

from airline import create_app
from airline.db import connect, initialize, query


@pytest.fixture
def app():
    return create_app({"TESTING": True, "SECRET_KEY": "test-only-key",
                       "MYSQL_HOST": os.getenv("TEST_MYSQL_HOST", "127.0.0.1"),
                       "MYSQL_PORT": os.getenv("TEST_MYSQL_PORT", "33317"),
                       "MYSQL_USER": os.getenv("TEST_MYSQL_USER", "root"),
                       "MYSQL_PASSWORD": os.getenv("TEST_MYSQL_PASSWORD", ""),
                       "MYSQL_DATABASE": "FlightManagement"})


@pytest.fixture
def database(app):
    if not os.getenv("TEST_MYSQL_PORT"):
        pytest.skip("Set TEST_MYSQL_PORT for a dedicated disposable MySQL server.")
    with app.app_context():
        admin = connect(server_only=True)
        marker = query(admin, "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='vivu_disposable_test_server'")
        if not marker:
            admin.close()
            pytest.fail("Refusing to reset: dedicated server marker vivu_disposable_test_server is absent.")
        # This server is explicitly designated for disposable tests, not the user's database.
        query(admin, "DROP DATABASE IF EXISTS FlightManagement")
        initialize(admin)
        admin.close()
        conn = connect()
        try:
            yield conn
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()
