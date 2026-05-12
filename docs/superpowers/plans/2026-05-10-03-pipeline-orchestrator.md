# AI Office — Chunk 3: Pipeline & Orchestrator

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 6-step approval pipeline — task router, approval chain state machine, Celery orchestrator, task/approval REST API, and WebSocket real-time updates. Owner submits task → PM decomposes → Level 3 workers execute → QA + Safety gate → Senior Lead reviews → CTO reviews → Owner sees final verdict.

**Architecture:** Celery worker runs `run_pipeline(task_id)` as async chain. ApprovalChain is a pure state machine (no DB calls) that returns step definitions. Each step writes an ApprovalStep row and broadcasts status via WebSocket. FastAPI routes expose task CRUD and approval history. WebSocket room keyed by task_id so owner gets live updates.

**Tech Stack:** Celery 5 + Redis broker, FastAPI WebSocket, SQLAlchemy async, all agents from Chunk 2

**Prerequisites:** Chunk 1 (auth, DB) + Chunk 2 (all agents) complete

---

## File Map

```
backend/app/
├── pipeline/
│   ├── __init__.py
│   ├── router.py            # route_task(task_type) → ordered list of steps
│   ├── approval_chain.py    # ApprovalChain: step definitions, transitions
│   └── orchestrator.py      # Celery task: run_pipeline(task_id)
├── api/
│   ├── tasks.py             # POST /tasks, GET /tasks, GET /tasks/{id}
│   ├── approvals.py         # GET /tasks/{id}/approvals
│   └── ws.py                # WebSocket /ws/tasks/{id}
├── services/
│   └── task_service.py      # create_task, get_task, list_tasks, update_status
├── schemas/
│   ├── task.py              # TaskCreate, TaskOut
│   └── approval.py          # ApprovalStepOut
└── worker.py                # Celery app init

backend/tests/
├── test_pipeline/
│   ├── __init__.py
│   ├── test_router.py
│   ├── test_approval_chain.py
│   └── test_orchestrator.py
├── test_tasks_api.py
└── test_ws.py
```

---

## Task 1: Task Router

**Files:**
- Create: `backend/app/pipeline/router.py`
- Test: `backend/tests/test_pipeline/test_router.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pipeline/test_router.py
from app.pipeline.router import route_task
from app.agents.roles import AgentRole

def test_full_stack_task_includes_all_devs():
    steps = route_task("full")
    roles = [s["role"] for s in steps]
    assert AgentRole.PRODUCT_MANAGER in roles
    assert AgentRole.FRONTEND_DEV in roles
    assert AgentRole.BACKEND_DEV in roles
    assert AgentRole.QA_ENGINEER in roles
    assert AgentRole.SAFETY_REVIEWER in roles
    assert AgentRole.SENIOR_LEAD in roles
    assert AgentRole.CTO in roles

def test_frontend_task_skips_backend():
    steps = route_task("frontend")
    roles = [s["role"] for s in steps]
    assert AgentRole.FRONTEND_DEV in roles
    assert AgentRole.BACKEND_DEV not in roles
    assert AgentRole.QA_ENGINEER in roles
    assert AgentRole.CTO in roles

def test_step_order_respected():
    steps = route_task("full")
    roles = [s["role"] for s in steps]
    pm_idx = roles.index(AgentRole.PRODUCT_MANAGER)
    qa_idx = roles.index(AgentRole.QA_ENGINEER)
    lead_idx = roles.index(AgentRole.SENIOR_LEAD)
    cto_idx = roles.index(AgentRole.CTO)
    assert pm_idx < qa_idx < lead_idx < cto_idx

def test_unknown_task_type_returns_full_pipeline():
    steps = route_task("unknown_type")
    assert len(steps) > 5
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/test_pipeline/test_router.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Write app/pipeline/router.py**

```python
from app.agents.roles import AgentRole

# Each step: {role, parallel_group}
# parallel_group=None → sequential. Same group int → run concurrently.
PIPELINES: dict[str, list[dict]] = {
    "full": [
        {"role": AgentRole.PRODUCT_MANAGER, "parallel_group": None},
        {"role": AgentRole.FRONTEND_DEV,    "parallel_group": 1},
        {"role": AgentRole.BACKEND_DEV,     "parallel_group": 1},
        {"role": AgentRole.API_ENGINEER,    "parallel_group": 1},
        {"role": AgentRole.DEVOPS,          "parallel_group": 1},
        {"role": AgentRole.QA_ENGINEER,     "parallel_group": 2},
        {"role": AgentRole.SAFETY_REVIEWER, "parallel_group": 2},
        {"role": AgentRole.SENIOR_LEAD,     "parallel_group": None},
        {"role": AgentRole.CTO,             "parallel_group": None},
    ],
    "frontend": [
        {"role": AgentRole.PRODUCT_MANAGER, "parallel_group": None},
        {"role": AgentRole.FRONTEND_DEV,    "parallel_group": None},
        {"role": AgentRole.QA_ENGINEER,     "parallel_group": 2},
        {"role": AgentRole.SAFETY_REVIEWER, "parallel_group": 2},
        {"role": AgentRole.SENIOR_LEAD,     "parallel_group": None},
        {"role": AgentRole.CTO,             "parallel_group": None},
    ],
    "backend": [
        {"role": AgentRole.PRODUCT_MANAGER, "parallel_group": None},
        {"role": AgentRole.BACKEND_DEV,     "parallel_group": 1},
        {"role": AgentRole.API_ENGINEER,    "parallel_group": 1},
        {"role": AgentRole.QA_ENGINEER,     "parallel_group": 2},
        {"role": AgentRole.SAFETY_REVIEWER, "parallel_group": 2},
        {"role": AgentRole.SENIOR_LEAD,     "parallel_group": None},
        {"role": AgentRole.CTO,             "parallel_group": None},
    ],
    "devops": [
        {"role": AgentRole.PRODUCT_MANAGER, "parallel_group": None},
        {"role": AgentRole.DEVOPS,          "parallel_group": None},
        {"role": AgentRole.QA_ENGINEER,     "parallel_group": 2},
        {"role": AgentRole.SAFETY_REVIEWER, "parallel_group": 2},
        {"role": AgentRole.SENIOR_LEAD,     "parallel_group": None},
        {"role": AgentRole.CTO,             "parallel_group": None},
    ],
    "data": [
        {"role": AgentRole.PRODUCT_MANAGER,  "parallel_group": None},
        {"role": AgentRole.DATA_EXTRACTOR,   "parallel_group": 1},
        {"role": AgentRole.RAG_SEARCH,       "parallel_group": 1},
        {"role": AgentRole.SAFETY_REVIEWER,  "parallel_group": None},
        {"role": AgentRole.SENIOR_LEAD,      "parallel_group": None},
        {"role": AgentRole.CTO,              "parallel_group": None},
    ],
}

def route_task(task_type: str) -> list[dict]:
    """Return ordered step list for task_type. Falls back to 'full'."""
    return PIPELINES.get(task_type, PIPELINES["full"])
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/test_pipeline/test_router.py -v
# Expected: 4 PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/router.py backend/tests/test_pipeline/test_router.py
git commit -m "feat: task router — 5 pipeline types with parallel group support"
```

---

## Task 2: Approval Chain State Machine

**Files:**
- Create: `backend/app/pipeline/approval_chain.py`
- Test: `backend/tests/test_pipeline/test_approval_chain.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pipeline/test_approval_chain.py
from app.pipeline.approval_chain import ApprovalChain, ChainState

def test_initial_state_pending():
    chain = ApprovalChain(task_id="t1", steps=[{"role": "cto", "parallel_group": None}])
    assert chain.state == ChainState.PENDING
    assert chain.current_step_index == 0

def test_advance_moves_to_next_step():
    chain = ApprovalChain(
        task_id="t1",
        steps=[
            {"role": "product_manager", "parallel_group": None},
            {"role": "cto", "parallel_group": None},
        ]
    )
    chain.start()
    assert chain.current_step_index == 0
    chain.advance("approved")
    assert chain.current_step_index == 1

def test_reject_terminates_chain():
    chain = ApprovalChain(
        task_id="t1",
        steps=[
            {"role": "product_manager", "parallel_group": None},
            {"role": "cto", "parallel_group": None},
        ]
    )
    chain.start()
    chain.advance("rejected")
    assert chain.state == ChainState.REJECTED
    assert chain.is_terminal()

def test_approve_all_steps_completes_chain():
    chain = ApprovalChain(
        task_id="t1",
        steps=[{"role": "cto", "parallel_group": None}]
    )
    chain.start()
    chain.advance("approved")
    assert chain.state == ChainState.APPROVED
    assert chain.is_terminal()
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/test_pipeline/test_approval_chain.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Write app/pipeline/approval_chain.py**

```python
from enum import Enum
from dataclasses import dataclass, field

class ChainState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass
class ApprovalChain:
    task_id: str
    steps: list[dict]
    state: ChainState = ChainState.PENDING
    current_step_index: int = 0
    history: list[dict] = field(default_factory=list)

    def start(self):
        if self.state != ChainState.PENDING:
            raise ValueError(f"Cannot start chain in state {self.state}")
        self.state = ChainState.RUNNING

    def current_step(self) -> dict | None:
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self, verdict: str) -> None:
        """
        verdict: 'approved' | 'revised' | 'rejected'
        - rejected → terminal REJECTED
        - approved + last step → terminal APPROVED
        - approved/revised + more steps → move to next
        """
        step = self.current_step()
        if step is None:
            return
        self.history.append({"step": self.current_step_index, "role": step["role"], "verdict": verdict})

        if verdict == "rejected":
            self.state = ChainState.REJECTED
            return

        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.state = ChainState.APPROVED
        # 'revised' keeps running, looping back is handled by orchestrator re-dispatching

    def is_terminal(self) -> bool:
        return self.state in (ChainState.APPROVED, ChainState.REJECTED)
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/test_pipeline/test_approval_chain.py -v
# Expected: 4 PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/approval_chain.py backend/tests/test_pipeline/test_approval_chain.py
git commit -m "feat: ApprovalChain state machine — pending/running/approved/rejected"
```

---

## Task 3: Celery Worker Setup

**Files:**
- Create: `backend/app/worker.py`
- Create: `backend/app/pipeline/__init__.py`

- [ ] **Step 1: Write app/worker.py**

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_office",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.pipeline.orchestrator"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,   # one task at a time — NIM calls are slow
    task_soft_time_limit=600,       # 10 min soft limit
    task_time_limit=660,            # 11 min hard limit
)
```

- [ ] **Step 2: Write app/pipeline/__init__.py**

```python
from app.pipeline.router import route_task
from app.pipeline.approval_chain import ApprovalChain, ChainState

__all__ = ["route_task", "ApprovalChain", "ChainState"]
```

- [ ] **Step 3: Verify Celery loads**

```bash
cd backend && celery -A app.worker inspect ping --timeout 2
# If Redis running: pong. If not: connection error — OK for now, Redis added in Chunk 5 infra
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/worker.py backend/app/pipeline/__init__.py
git commit -m "feat: Celery app init with Redis broker, conservative task limits"
```

---

## Task 4: Pipeline Orchestrator

**Files:**
- Create: `backend/app/pipeline/orchestrator.py`
- Test: `backend/tests/test_pipeline/test_orchestrator.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pipeline/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.pipeline.orchestrator import execute_step

@pytest.mark.asyncio
async def test_execute_step_product_manager():
    mock_db = AsyncMock()
    mock_task = MagicMock()
    mock_task.description = "Build a login page"
    mock_task.task_type = "frontend"

    with patch("app.pipeline.orchestrator.ProductManagerAgent") as MockPM:
        instance = AsyncMock()
        instance.decompose.return_value = MagicMock(
            title="Login Page",
            description="React login form",
            acceptance_criteria=["Shows email+password fields"],
            subtasks=[],
            priority="high",
            estimated_complexity=2,
        )
        MockPM.return_value = instance

        result = await execute_step(
            role="product_manager",
            task=mock_task,
            previous_outputs={},
            db=mock_db,
        )
        assert "title" in result or "description" in result or isinstance(result, str)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/test_pipeline/test_orchestrator.py -v
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Write app/pipeline/orchestrator.py**

```python
import asyncio
import json
import logging
from datetime import datetime, timezone
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.config import settings
from app.worker import celery_app
from app.models.task import Task, TaskStatus
from app.models.approval_step import ApprovalStep, StepStatus
from app.pipeline.router import route_task
from app.pipeline.approval_chain import ApprovalChain, ChainState
from app.agents.roles import AgentRole
from app.agents.product_manager_agent import ProductManagerAgent
from app.agents.senior_lead_agent import SeniorLeadAgent
from app.agents.cto_agent import CTOAgent
from app.agents.frontend_dev_agent import FrontendDevAgent
from app.agents.backend_dev_agent import BackendDevAgent
from app.agents.api_engineer_agent import APIEngineerAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.qa_engineer_agent import QAEngineerAgent
from app.agents.safety_reviewer_agent import SafetyReviewerAgent
from app.agents.data_extractor_agent import DataExtractorAgent
from app.agents.rag_search_agent import RAGSearchAgent

logger = logging.getLogger(__name__)

AGENT_MAP = {
    AgentRole.PRODUCT_MANAGER: ProductManagerAgent,
    AgentRole.SENIOR_LEAD: SeniorLeadAgent,
    AgentRole.CTO: CTOAgent,
    AgentRole.FRONTEND_DEV: FrontendDevAgent,
    AgentRole.BACKEND_DEV: BackendDevAgent,
    AgentRole.API_ENGINEER: APIEngineerAgent,
    AgentRole.DEVOPS: DevOpsAgent,
    AgentRole.QA_ENGINEER: QAEngineerAgent,
    AgentRole.SAFETY_REVIEWER: SafetyReviewerAgent,
    AgentRole.DATA_EXTRACTOR: DataExtractorAgent,
    AgentRole.RAG_SEARCH: RAGSearchAgent,
}

def _make_session():
    engine = create_async_engine(settings.DATABASE_URL)
    return async_sessionmaker(engine, expire_on_commit=False)

async def execute_step(role: str, task: Task, previous_outputs: dict, db: AsyncSession) -> str:
    """Run one agent step. Returns string output."""
    agent_role = AgentRole(role)
    AgentClass = AGENT_MAP[agent_role]
    agent = AgentClass()
    combined_context = "\n\n".join(f"[{r}]: {o}" for r, o in previous_outputs.items())

    if agent_role == AgentRole.PRODUCT_MANAGER:
        result = await agent.decompose(task.description)
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.CTO:
        result = await agent.review(combined_context or task.description, task_title=task.title)
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.SENIOR_LEAD:
        result = await agent.coordinate(task.description, previous_outputs if previous_outputs else None)
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.QA_ENGINEER:
        result = await agent.test(combined_context, task.description)
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.SAFETY_REVIEWER:
        result = await agent.review(combined_context or task.description)
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.FRONTEND_DEV:
        result = await agent.build(previous_outputs.get("product_manager", task.description))
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.BACKEND_DEV:
        result = await agent.implement(previous_outputs.get("product_manager", task.description))
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.API_ENGINEER:
        result = await agent.design(previous_outputs.get("product_manager", task.description))
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.DEVOPS:
        result = await agent.configure(previous_outputs.get("product_manager", task.description))
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.DATA_EXTRACTOR:
        result = await agent.extract(task.description)
        return json.dumps(asdict(result))
    elif agent_role == AgentRole.RAG_SEARCH:
        result = await agent.search(task.description, list(previous_outputs.values()))
        return json.dumps(asdict(result))
    else:
        raise ValueError(f"No execute handler for role: {role}")

def _extract_verdict(role: str, output_json: str) -> str:
    """Pull approval verdict from agent output. Returns 'approved'|'rejected'|'revised'."""
    try:
        data = json.loads(output_json)
    except Exception:
        return "approved"  # non-verdict agents always pass through

    if role == AgentRole.CTO.value:
        v = data.get("verdict", "APPROVE").upper()
        return {"APPROVE": "approved", "REJECT": "rejected", "REVISE": "revised"}.get(v, "approved")
    if role == AgentRole.QA_ENGINEER.value:
        return "approved" if data.get("verdict", "PASS") == "PASS" else "revised"
    if role == AgentRole.SAFETY_REVIEWER.value:
        return "approved" if data.get("approved", True) else "rejected"
    return "approved"

@celery_app.task(bind=True, name="pipeline.run")
def run_pipeline(self, task_id: str):
    """Celery entry point — runs full pipeline for a task."""
    asyncio.run(_run_pipeline_async(task_id))

async def _run_pipeline_async(task_id: str):
    SessionLocal = _make_session()
    async with SessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            logger.error(f"Task {task_id} not found")
            return

        steps = route_task(task.task_type)
        chain = ApprovalChain(task_id=task_id, steps=steps)
        chain.start()

        task.status = TaskStatus.IN_PROGRESS
        await db.commit()

        previous_outputs: dict[str, str] = {}

        # Group steps by parallel_group
        i = 0
        step_number = 1
        while i < len(steps) and not chain.is_terminal():
            step = steps[i]
            group = step.get("parallel_group")

            # Collect all steps in same parallel group
            parallel_steps = [step]
            j = i + 1
            while j < len(steps) and steps[j].get("parallel_group") == group and group is not None:
                parallel_steps.append(steps[j])
                j += 1

            # Create ApprovalStep rows
            db_steps = []
            for ps in parallel_steps:
                db_step = ApprovalStep(
                    task_id=task_id,
                    step_number=step_number,
                    agent_role=ps["role"].value,
                    status=StepStatus.RUNNING,
                    started_at=datetime.now(timezone.utc),
                )
                db.add(db_step)
                db_steps.append((ps, db_step))
                step_number += 1
            await db.commit()

            # Execute parallel or sequential
            if len(parallel_steps) > 1:
                results = await asyncio.gather(
                    *[execute_step(ps["role"].value, task, previous_outputs, db) for ps, _ in db_steps],
                    return_exceptions=True,
                )
            else:
                try:
                    results = [await execute_step(parallel_steps[0]["role"].value, task, previous_outputs, db)]
                except Exception as e:
                    results = [e]

            # Record outputs and compute verdicts
            group_verdict = "approved"
            for (ps, db_step), result in zip(db_steps, results):
                if isinstance(result, Exception):
                    logger.error(f"Step {ps['role']} failed: {result}")
                    db_step.status = StepStatus.REJECTED
                    db_step.output = str(result)
                    db_step.verdict = "ERROR"
                    group_verdict = "rejected"
                else:
                    verdict = _extract_verdict(ps["role"].value, result)
                    db_step.output = result
                    db_step.verdict = verdict.upper()
                    db_step.status = (
                        StepStatus.APPROVED if verdict == "approved"
                        else StepStatus.REVISED if verdict == "revised"
                        else StepStatus.REJECTED
                    )
                    db_step.finished_at = datetime.now(timezone.utc)
                    previous_outputs[ps["role"].value] = result
                    if verdict == "rejected":
                        group_verdict = "rejected"
                    elif verdict == "revised" and group_verdict == "approved":
                        group_verdict = "revised"

            await db.commit()
            chain.advance(group_verdict)
            i = j if group is not None else i + 1

        # Final task status
        task.status = TaskStatus.APPROVED if chain.state == ChainState.APPROVED else TaskStatus.REJECTED
        await db.commit()
        logger.info(f"Pipeline complete for task {task_id}: {task.status}")
```

- [ ] **Step 4: Run test**

```bash
python -m pytest tests/test_pipeline/test_orchestrator.py -v
# Expected: PASSED
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/orchestrator.py backend/tests/test_pipeline/
git commit -m "feat: pipeline orchestrator — Celery task, parallel step execution, verdict extraction"
```

---

## Task 5: Task Service + Schemas

**Files:**
- Create: `backend/app/services/task_service.py`
- Create: `backend/app/schemas/task.py`
- Create: `backend/app/schemas/approval.py`
- Test: `backend/tests/test_tasks_api.py`

- [ ] **Step 1: Write app/schemas/task.py**

```python
from pydantic import BaseModel
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str
    task_type: str = "full"   # full | frontend | backend | devops | data

class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    task_type: str
    status: str
    created_by: str
    created_at: datetime
    celery_task_id: str | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Write app/schemas/approval.py**

```python
from pydantic import BaseModel
from datetime import datetime

class ApprovalStepOut(BaseModel):
    id: str
    task_id: str
    step_number: int
    agent_role: str
    status: str
    output: str | None
    verdict: str | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Write app/services/task_service.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate

async def create_task(db: AsyncSession, body: TaskCreate, user_id: str) -> Task:
    task = Task(
        title=body.title,
        description=body.description,
        task_type=body.task_type,
        status=TaskStatus.PENDING,
        created_by=user_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

async def get_task(db: AsyncSession, task_id: str) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def list_tasks(db: AsyncSession, user_id: str) -> list[Task]:
    result = await db.execute(select(Task).where(Task.created_by == user_id).order_by(Task.created_at.desc()))
    return list(result.scalars().all())

async def update_task_celery_id(db: AsyncSession, task: Task, celery_id: str) -> Task:
    task.celery_task_id = celery_id
    await db.commit()
    return task
```

- [ ] **Step 4: Write app/api/tasks.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user, require_owner
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut
from app.services.task_service import create_task, get_task, list_tasks, update_task_celery_id
from app.pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskOut, status_code=201)
async def submit_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_owner),
):
    task = await create_task(db, body, user.id)
    celery_result = run_pipeline.delay(task.id)
    await update_task_celery_id(db, task, celery_result.id)
    return TaskOut.model_validate(task)

@router.get("", response_model=list[TaskOut])
async def list_my_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tasks = await list_tasks(db, user.id)
    return [TaskOut.model_validate(t) for t in tasks]

@router.get("/{task_id}", response_model=TaskOut)
async def get_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await get_task(db, task_id)
    if task is None or task.created_by != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(task)
```

- [ ] **Step 5: Write app/api/approvals.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.approval_step import ApprovalStep
from app.schemas.approval import ApprovalStepOut
from app.services.task_service import get_task

router = APIRouter(prefix="/tasks", tags=["approvals"])

@router.get("/{task_id}/approvals", response_model=list[ApprovalStepOut])
async def get_approvals(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await get_task(db, task_id)
    if task is None or task.created_by != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    result = await db.execute(
        select(ApprovalStep).where(ApprovalStep.task_id == task_id).order_by(ApprovalStep.step_number)
    )
    return [ApprovalStepOut.model_validate(s) for s in result.scalars().all()]
```

- [ ] **Step 6: Write app/api/ws.py (WebSocket real-time)**

```python
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.approval_step import ApprovalStep
from app.services.task_service import get_task

router = APIRouter(tags=["websocket"])

# In-memory connection registry: task_id → list of WebSocket
_connections: dict[str, list[WebSocket]] = {}

async def broadcast(task_id: str, data: dict):
    """Send update to all clients watching task_id."""
    dead = []
    for ws in _connections.get(task_id, []):
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections[task_id].remove(ws)

@router.websocket("/ws/tasks/{task_id}")
async def task_updates(task_id: str, ws: WebSocket, db: AsyncSession = Depends(get_db)):
    await ws.accept()
    _connections.setdefault(task_id, []).append(ws)

    # Send current state immediately on connect
    task = await get_task(db, task_id)
    if task:
        steps_result = await db.execute(
            select(ApprovalStep).where(ApprovalStep.task_id == task_id).order_by(ApprovalStep.step_number)
        )
        steps = [{"step": s.step_number, "role": s.agent_role, "status": s.status, "verdict": s.verdict}
                 for s in steps_result.scalars().all()]
        await ws.send_json({"type": "state", "task_status": task.status, "steps": steps})

    try:
        while True:
            await asyncio.sleep(2)
            # Ping to keep alive
            await ws.send_json({"type": "ping"})
    except WebSocketDisconnect:
        if task_id in _connections:
            try:
                _connections[task_id].remove(ws)
            except ValueError:
                pass
```

- [ ] **Step 7: Update main.py to include all routers**

```python
# Add to backend/app/main.py imports and router includes:
from app.api.tasks import router as tasks_router
from app.api.approvals import router as approvals_router
from app.api.ws import router as ws_router

# Add after auth_router include:
app.include_router(tasks_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(ws_router)
```

- [ ] **Step 8: Write failing test**

```python
# backend/tests/test_tasks_api.py
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_submit_task_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/tasks", json={"title": "Test", "description": "Do X", "task_type": "frontend"})
        assert r.status_code == 403  # no bearer token

@pytest.mark.asyncio
async def test_list_tasks_returns_empty_for_new_user(auth_client):
    r = await auth_client.get("/api/tasks")
    assert r.status_code == 200
    assert r.json() == []
```

- [ ] **Step 9: Add auth_client fixture to conftest.py**

```python
# Add to backend/tests/conftest.py:
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def auth_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={"email": "test@x.com", "password": "pass123"})
        r = await client.post("/auth/login", json={"email": "test@x.com", "password": "pass123"})
        token = r.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
```

- [ ] **Step 10: Run — expect PASS**

```bash
python -m pytest tests/test_tasks_api.py -v
# Expected: 2 PASSED
```

- [ ] **Step 11: Commit**

```bash
git add backend/app/api/ backend/app/services/task_service.py backend/app/schemas/ backend/tests/test_tasks_api.py
git commit -m "feat: task + approval API routes, WebSocket live updates"
```

---

## Chunk 3 Complete

All tasks done when:
- `pytest backend/tests/ -v` → all green
- `POST /api/tasks` creates task + fires Celery job
- `GET /api/tasks/{id}/approvals` returns step-by-step pipeline state
- `WebSocket /ws/tasks/{id}` receives ping every 2s
- Orchestrator runs all agent steps, writes verdicts to DB

**Next:** Chunk 4 — Frontend Dashboard (React)
