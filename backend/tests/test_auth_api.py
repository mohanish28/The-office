import pytest


@pytest.mark.asyncio
async def test_register_and_login(app_client):
    r = await app_client.post("/api/auth/register", json={"email": "owner@test.com", "password": "secret123"})
    assert r.status_code == 201
    assert r.json()["is_owner"] is True

    r2 = await app_client.post("/api/auth/login", json={"email": "owner@test.com", "password": "secret123"})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.asyncio
async def test_login_wrong_password(app_client):
    await app_client.post("/api/auth/register", json={"email": "owner@test.com", "password": "secret123"})
    r = await app_client.post("/api/auth/login", json={"email": "owner@test.com", "password": "wrong"})
    assert r.status_code == 401
