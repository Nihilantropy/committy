"""Pytest configuration file for Committy tests."""

import os
import json
import pytest
from unittest.mock import patch


@pytest.fixture
def test_fixtures_dir():
    """Return the path to the test fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def feature_addition_diff(test_fixtures_dir):
    """Load the feature addition diff fixture."""
    with open(os.path.join(test_fixtures_dir, "feature_addition.diff"), "r") as f:
        return f.read()


@pytest.fixture
def feature_addition_expected(test_fixtures_dir):
    """Load the expected message for feature addition fixture."""
    with open(os.path.join(test_fixtures_dir, "feature_addition.expected.txt"), "r") as f:
        return f.read().strip()


@pytest.fixture
def bug_fix_diff(test_fixtures_dir):
    """Load the bug fix diff fixture."""
    with open(os.path.join(test_fixtures_dir, "bug_fix.diff"), "r") as f:
        return f.read()


@pytest.fixture
def bug_fix_expected(test_fixtures_dir):
    """Load the expected message for bug fix fixture."""
    with open(os.path.join(test_fixtures_dir, "bug_fix.expected.txt"), "r") as f:
        return f.read().strip()


@pytest.fixture
def test_suite(test_fixtures_dir):
    """Load the complete test suite definition."""
    with open(os.path.join(test_fixtures_dir, "test_suite.json"), "r") as f:
        return json.load(f)


@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client for testing."""
    import unittest.mock as mock
    
    client = mock.MagicMock()
    client.is_running.return_value = True
    client.has_model.return_value = True
    client.generate.return_value = "Generated commit message"
    
    return client

@pytest.fixture(autouse=True)
def setup_testing_env():
    """Set up testing environment for all tests."""
    with patch.dict(os.environ, {"IS_TESTING": "1"}):
        yield