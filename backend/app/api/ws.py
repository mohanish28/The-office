import asyncio
import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.approval_step import ApprovalStep
from app.models.task import Task
from app.services.auth_service import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

_connections: dict[str, set[WebSocket]] = {}


async def broadcast(task_id: str, data: dict) -> None:
    if task_id not in _connections:
        return
    dead: list[WebSocket] = []
    payload = json.dumps(data)
    for ws in _connections[task_id]:
        try:
            await ws.send_text(payload)
        except (WebSocketDisconnect, RuntimeError):
            dead.append(ws)
    for ws in dead:
        _connections[task_id].discard(ws)
    if not _connections[task_id]:
        del _connections[task_id]


@router.websocket("/ws/tasks/{task_id}")
async def ws_task(
    websocket: WebSocket,
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    token = websocket.query_params.get("token")
    if token:
        try:
            decode_access_token(token)
        except ValueError:
            await websocket.close(code=1008, reason="Invalid or expired token")
            return
    else:
        await websocket.close(code=1008, reason="Missing token")
        return

    await websocket.accept()

    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            await websocket.send_text(json.dumps({
                "type": "state",
                "task_id": task_id,
                "status": "not_found",
                "steps": [],
            }))
            return

        _connections.setdefault(task_id, set()).add(websocket)

        result = await db.execute(
            select(ApprovalStep)
            .where(ApprovalStep.task_id == task_id)
            .order_by(ApprovalStep.step_number)
        )
        steps = list(result.scalars().all())

        await websocket.send_text(json.dumps({
            "type": "state",
            "task_id": task_id,
            "status": task.status,
            "steps": [
                {
                    "agent_role": s.agent_role,
                    "status": s.status,
                    "verdict": s.verdict,
                }
                for s in steps
            ],
        }))

        while True:
            await asyncio.sleep(2)
            await websocket.send_text(json.dumps({"type": "ping", "task_id": task_id}))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        _connections.get(task_id, set()).discard(websocket)
        if task_id in _connections and not _connections[task_id]:
            del _connections[task_id]
