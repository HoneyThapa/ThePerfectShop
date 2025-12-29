"""
Test configuration and fixtures
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the database session to avoid database dependencies in tests
@pytest.fixture(autouse=True)
def mock_database():
    """Mock database session for all tests"""
    with patch('app.db.session.SessionLocal') as mock_session:
        mock_session.return_value = Mock()
        yield mock_session