from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def _owner_token(app_client: AsyncClient) -> str:
    await app_client.post("/api/auth/register", json={"email": "owner@test.com", "password": "pw"})
    resp = await app_client.post("/api/auth/login", json={"email": "owner@test.com", "password": "pw"})
    token = resp.json()["access_token"]

    from app.database import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "owner@test.com"))
        user = result.scalar_one()
        user.is_owner = True
        await db.commit()

    return token


@pytest_asyncio.fixture
async def _user_token(app_client: AsyncClient) -> str:
    await app_client.post("/api/auth/register", json={"email": "user@test.com", "password": "pw"})
    resp = await app_client.post("/api/auth/login", json={"email": "user@test.com", "password": "pw"})
    token = resp.json()["access_token"]

    from app.database import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "user@test.com"))
        user = result.scalar_one()
        user.is_owner = False
        await db.commit()

    return token


@pytest.mark.asyncio
async def test_create_task_owner(app_client: AsyncClient, _owner_token):
    with patch("app.worker.run_pipeline") as mock_run:
        mock_run.delay.return_value = MagicMock(id="celery-123")
        resp = await app_client.post(
            "/api/tasks",
            json={"title": "t", "description": "d", "task_type": "full"},
            headers={"Authorization": f"Bearer {_owner_token}"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["celery_task_id"] == "celery-123"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_task_non_owner(app_client: AsyncClient, _user_token):
    resp = await app_client.post(
        "/api/tasks",
        json={"title": "t", "description": "d", "task_type": "full"},
        headers={"Authorization": f"Bearer {_user_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_task_unauthenticated(app_client: AsyncClient):
    resp = await app_client.post(
        "/api/tasks",
        json={"title": "t", "description": "d", "task_type": "full"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_task_owner(app_client: AsyncClient, _owner_token):
    with patch("app.worker.run_pipeline") as mock_run:
        mock_run.delay.return_value = MagicMock(id="celery-123")
        create_resp = await app_client.post(
            "/api/tasks",
            json={"title": "t", "description": "d", "task_type": "full"},
            headers={"Authorization": f"Bearer {_owner_token}"},
        )
    task_id = create_resp.json()["id"]

    resp = await app_client.get(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {_owner_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_not_found(app_client: AsyncClient, _owner_token):
    resp = await app_client.get(
        "/api/tasks/nonexistent",
        headers={"Authorization": f"Bearer {_owner_token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_task_wrong_user(app_client: AsyncClient, _owner_token, _user_token):
    with patch("app.worker.run_pipeline") as mock_run:
        mock_run.delay.return_value = MagicMock(id="celery-123")
        create_resp = await app_client.post(
            "/api/tasks",
            json={"title": "t", "description": "d", "task_type": "full"},
            headers={"Authorization": f"Bearer {_owner_token}"},
        )
    task_id = create_resp.json()["id"]

    resp = await app_client.get(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {_user_token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_approvals_empty(app_client: AsyncClient, _owner_token):
    with patch("app.worker.run_pipeline") as mock_run:
        mock_run.delay.return_value = MagicMock(id="celery-123")
        create_resp = await app_client.post(
            "/api/tasks",
            json={"title": "t", "description": "d", "task_type": "full"},
            headers={"Authorization": f"Bearer {_owner_token}"},
        )
    task_id = create_resp.json()["id"]

    resp = await app_client.get(
        f"/api/tasks/{task_id}/approvals",
        headers={"Authorization": f"Bearer {_owner_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []
