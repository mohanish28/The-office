import pytest


@pytest.mark.asyncio
async def test_health_endpoint(app_client):
    r = await app_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "ai-office-backend"}
