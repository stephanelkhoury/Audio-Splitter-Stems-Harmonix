"""
Pytest configuration and fixtures
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_audio_path(test_data_dir):
    """Path to sample audio file for testing"""
    # This would be a real audio file in production tests
    return test_data_dir / "sample.wav"


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests requiring GPU"
    )
