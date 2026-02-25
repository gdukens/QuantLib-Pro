"""Test configuration and utilities."""

import pytest
import numpy as np


@pytest.fixture
def sample_times():
    """Standard time array for testing."""
    return np.linspace(0, 1, 101)


@pytest.fixture
def random_state():
    """Fixed random state for reproducible tests."""
    return 42