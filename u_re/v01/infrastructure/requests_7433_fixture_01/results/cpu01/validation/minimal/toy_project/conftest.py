import pytest
@pytest.fixture
def httpbin(httpbin):
    return "wrapped:" + httpbin
@pytest.fixture
def httpbin_secure(httpbin_secure):
    return "wrapped:" + httpbin_secure
