"""
Shared pytest fixtures for discounts service tests.
"""
import os
import sys
import importlib
import pytest
from unittest.mock import patch, Mock


@pytest.fixture(scope="module")
def client():
    """
    Provides a Flask test client for the discounts app, while ensuring:
    - POSTGRES_* env vars exist before importing discounts.py
    - bootstrap.db is patched during the import to prevent real DB init
    - Module is loaded once per test module for better performance
    """
    # Set env vars directly (module scope, so monkeypatch not available)
    os.environ["POSTGRES_USER"] = "test_user"
    os.environ["POSTGRES_PASSWORD"] = "test_password"
    os.environ["POSTGRES_HOST"] = "test_host"

    # Ensure we're importing the local module
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # If discounts was already imported for any reason, reload cleanly
    sys.modules.pop("discounts", None)

    # Patch bootstrap.db during import of discounts
    with patch("bootstrap.db") as mock_db:
        mock_db.init_app = Mock()
        mock_db.drop_all = Mock()
        mock_db.create_all = Mock()
        mock_db.session = Mock()

        discounts_module = importlib.import_module("discounts")
        app = discounts_module.app

    test_client = app.test_client()
    app.testing = True
    return test_client


@pytest.fixture
def mock_discount_factory():
    """
    Factory fixture for creating mock discount objects with minimal data.
    Only includes fields that are commonly tested.
    """
    def _create_mock(id=1, name="Test Discount", code="TEST20", value=20):
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.serialize.return_value = {
            "id": id,
            "name": name,
            "code": code,
            "value": value,
        }
        return mock
    return _create_mock
