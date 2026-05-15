import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.roles import (
    BackendDev,
    CTOAgent,
    DataExtractor,
    DevOps,
    FrontendDev,
    PMAgent,
    QAReviewer,
    SafetyReviewer,
    SeniorLead,
)
from app.database import AsyncSessionLocal
from app.models.approval_step import ApprovalStep, StepStatus
from app.models.task import Task, TaskStatus
from app.pipeline.chain import ApprovalChain
from app.pipeline.router import route_task

ROLE_AGENT_MAP = {
    "PM": PMAgent,
    "BackendDev": BackendDev,
    "FrontendDev": FrontendDev,
    "DevOps": DevOps,
    "DataEngineer": DataExtractor,
    "SeniorLead": SeniorLead,
    "QA": QAReviewer,
    "Safety": SafetyReviewer,
    "CTO": CTOAgent,
}


logger = logging.getLogger(__name__)


def _extract_verdict(role: str, result: dataclass) -> str:
    if role == "CTO":
        verdict = getattr(result, "verdict", "")
        if verdict == "APPROVE":
            return "approved"
        if verdict == "REVISE":
            return "revised"
        logger.warning("CTO returned unknown verdict %r, treating as rejected", verdict)
        return "rejected"
    if role == "QA":
        passed = getattr(result, "passed", False)
        return "approved" if passed else "rejected"
    if role == "Safety":
        approved = getattr(result, "approved", False)
        return "approved" if approved else "rejected"
    return "approved"


async def _run_agent(role: str, context: dict) -> dataclass:
    agent_cls = ROLE_AGENT_MAP[role]
    agent = agent_cls()
    return await agent.run(context)


def _chain_snapshot(task_id: str, chain: ApprovalChain, steps: list[ApprovalStep]) -> dict:
    return {
        "type": "state",
        "task_id": task_id,
        "status": chain.state,
        "steps": [
            {
                "agent_role": s.agent_role,
                "status": s.status,
                "verdict": s.verdict,
            }
            for s in steps
        ],
    }


async def _run_pipeline_async(task_id: str) -> None:
    from app.api.ws import broadcast

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return

        task.status = TaskStatus.IN_PROGRESS
        await db.commit()

        context = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
        }

        step_groups = route_task(task.task_type)
        chain = ApprovalChain(steps=step_groups)
        chain.start()

        all_step_rows: list[ApprovalStep] = []
        step_number = 0

        try:
            while not chain.is_terminal():
                group = chain.current_group()
                if group is None:
                    break

                step_rows: list[ApprovalStep] = []
                for role in group:
                    step_number += 1
                    step_row = ApprovalStep(
                        task_id=task_id,
                        step_number=step_number,
                        agent_role=role,
                        status=StepStatus.RUNNING,
                        started_at=datetime.now(timezone.utc),
                    )
                    db.add(step_row)
                    step_rows.append(step_row)
                await db.commit()
                all_step_rows.extend(step_rows)

                results = await asyncio.gather(
                    *[_run_agent(role, context) for role in group],
                    return_exceptions=True,
                )

                group_verdict = "approved"
                details: list[dict] = []
                for role, step_row, result in zip(group, step_rows, results):
                    if isinstance(result, Exception):
                        verdict = "rejected"
                        output = str(result)
                    else:
                        verdict = _extract_verdict(role, result)
                        output = json.dumps(
                            {k: v for k, v in result.__dict__.items()},
                            default=str,
                        )

                    step_row.verdict = verdict
                    step_row.output = output
                    step_row.finished_at = datetime.now(timezone.utc)
                    if verdict == "approved":
                        step_row.status = StepStatus.APPROVED
                    elif verdict == "revised":
                        step_row.status = StepStatus.REVISED
                    else:
                        step_row.status = StepStatus.REJECTED

                    details.append({"role": role, "verdict": verdict})
                    if verdict == "rejected":
                        group_verdict = "rejected"
                    elif verdict == "revised" and group_verdict != "rejected":
                        group_verdict = "revised"

                await db.commit()

                chain.record_group_verdict(group_verdict, details)

                await broadcast(task_id, _chain_snapshot(task_id, chain, all_step_rows))

            task.status = TaskStatus.APPROVED if chain.state == "APPROVED" else TaskStatus.REJECTED
            await db.commit()
        except Exception:
            task.status = TaskStatus.REJECTED
            await db.commit()
            raise
