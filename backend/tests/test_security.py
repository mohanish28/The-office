import pytest


@pytest.mark.asyncio
async def test_security_headers_present(app_client):
    r = await app_client.get("/api/auth/login")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("strict-transport-security") is not None
