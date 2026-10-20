import pytest
@pytest.fixture
def httpbin():
    return "SYNTHETIC-PLAIN"
@pytest.fixture
def httpbin_secure():
    return "SYNTHETIC-SECURE"
