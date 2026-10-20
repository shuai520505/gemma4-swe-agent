def test_plain(httpbin):
    assert httpbin == "wrapped:SYNTHETIC-PLAIN"
def test_secure(httpbin_secure):
    assert httpbin_secure == "wrapped:SYNTHETIC-SECURE"
