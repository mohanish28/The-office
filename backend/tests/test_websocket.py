import json

import pytest
from unittest.mock import MagicMock, patch

import app.database as db_module
from app.models.user import User
from sqlalchemy import select


def _make_owner(sync_app_client, email):
    sync_app_client.post("/api/auth/register", json={"email": email, "password": "pw"})
    login_resp = sync_app_client.post("/api/auth/login", json={"email": email, "password": "pw"})
    token = login_resp.json()["access_token"]

    import asyncio

    async def _set_owner():
        async with db_module.AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one()
            user.is_owner = True
            await db.commit()

    asyncio.run(_set_owner())
    return token


def test_ws_connect_sends_state(sync_app_client):
    token = _make_owner(sync_app_client, "ws@test.com")

    with patch("app.worker.run_pipeline") as mock_run:
        mock_run.delay.return_value = MagicMock(id="celery-123")
        create_resp = sync_app_client.post(
            "/api/tasks",
            json={"title": "t", "description": "d", "task_type": "full"},
            headers={"Authorization": f"Bearer {token}"},
        )
    task_id = create_resp.json()["id"]

    with sync_app_client.websocket_connect(f"/ws/tasks/{task_id}?token={token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "state"
        assert data["task_id"] == task_id


def test_ws_ping(sync_app_client):
    token = _make_owner(sync_app_client, "ws2@test.com")

    with patch("app.worker.run_pipeline") as mock_run:
        mock_run.delay.return_value = MagicMock(id="celery-123")
        create_resp = sync_app_client.post(
            "/api/tasks",
            json={"title": "t", "description": "d", "task_type": "full"},
            headers={"Authorization": f"Bearer {token}"},
        )
    task_id = create_resp.json()["id"]

    with sync_app_client.websocket_connect(f"/ws/tasks/{task_id}?token={token}") as websocket:
        websocket.receive_json()
        data = websocket.receive_json()
        assert data["type"] == "ping"
        assert data["task_id"] == task_id


def test_ws_unknown_task(sync_app_client):
    token = _make_owner(sync_app_client, "ws3@test.com")

    with sync_app_client.websocket_connect(f"/ws/tasks/nonexistent-ws?token={token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "state"
        assert data["status"] == "not_found"


def test_ws_missing_token(sync_app_client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with sync_app_client.websocket_connect("/ws/tasks/any-id"):
            pass
