"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import pytest


# Set a dummy API key for tests that don't actually call the API
os.environ.setdefault("PORTKEY_API_KEY", "test-key-for-unit-tests")


@pytest.fixture
def fixtures_path() -> Path:
    """Path to test fixtures."""
    return Path(__file__).parent / "fixtures" / "sample_code"


@pytest.fixture
def vulnerable_code(fixtures_path: Path) -> str:
    """Load vulnerable code sample."""
    return (fixtures_path / "vulnerable_code.py").read_text()


@pytest.fixture
def complex_code(fixtures_path: Path) -> str:
    """Load complex code sample."""
    return (fixtures_path / "complex_code.py").read_text()


@pytest.fixture
def undocumented_code(fixtures_path: Path) -> str:
    """Load undocumented code sample."""
    return (fixtures_path / "undocumented_code.py").read_text()


@pytest.fixture
def slow_code(fixtures_path: Path) -> str:
    """Load slow code sample."""
    return (fixtures_path / "slow_code.py").read_text()


@pytest.fixture
def clean_code(fixtures_path: Path) -> str:
    """Load clean code sample."""
    return (fixtures_path / "clean_code.py").read_text()


@pytest.fixture
def mixed_issues_code(fixtures_path: Path) -> str:
    """Load mixed issues code sample."""
    return (fixtures_path / "mixed_issues.py").read_text()
