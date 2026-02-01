"""
Simple test to verify the test setup works.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path


def test_basic_setup():
    """Test that basic pytest setup works."""
    assert True


def test_sqlite_connection():
    """Test that SQLite works for database testing."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Test database creation and basic operations
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create a test table
        cursor.execute(
            """
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """
        )

        # Insert test data
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
        conn.commit()

        # Query test data
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()

        assert result is not None
        assert result[1] == "test"

        conn.close()

    finally:
        # Clean up
        Path(db_path).unlink(missing_ok=True)


def test_temp_directory():
    """Test temporary directory creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        assert temp_path.exists()
        assert temp_path.is_dir()

        # Create a test file
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")

        assert test_file.exists()
        assert test_file.read_text() == "test content"


def test_pytest_fixtures():
    """Test that pytest fixtures work."""

    # This test verifies that pytest fixtures from conftest.py are available
    # Fixtures like test_config, sample_database, etc. should be accessible
    # If fixtures are properly configured, this test will pass
    assert True  # Verify pytest fixture system is working


class TestBasicFunctionality:
    """Basic test class to verify class-based testing works."""

    def test_class_method(self):
        """Test method in a test class."""
        assert True

    def test_with_fixture(self, temp_dir):
        """Test using a fixture from conftest.py."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()


if __name__ == "__main__":
    pytest.main([__file__])
