from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_owner
from app.database import get_db
from app.models.approval_step import ApprovalStep
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.tasks import ApprovalStepResponse, TaskCreate, TaskResponse
from app.security.rate_limiter import limiter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
@limiter.limit("10/minute")
async def create_task(
    body: TaskCreate,
    request: Request,
    user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    task = Task(
        title=body.title,
        description=body.description,
        task_type=body.task_type,
        status=TaskStatus.PENDING,
        created_by=user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    from app.worker import run_pipeline

    result = run_pipeline.delay(task.id)
    task.celery_task_id = result.id
    await db.commit()
    await db.refresh(task)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None or task.created_by != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/approvals", response_model=list[ApprovalStepResponse])
async def get_approvals(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None or task.created_by != user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(ApprovalStep)
        .where(ApprovalStep.task_id == task_id)
        .order_by(ApprovalStep.step_number)
    )
    return list(result.scalars().all())
