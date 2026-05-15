from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str
    task_type: str


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    task_type: str
    status: str
    created_by: str
    created_at: datetime
    celery_task_id: str | None
    model_config = ConfigDict(from_attributes=True)


class ApprovalStepResponse(BaseModel):
    id: str
    task_id: str
    step_number: int
    agent_role: str
    status: str
    output: str | None
    verdict: str | None
    started_at: datetime | None
    finished_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
