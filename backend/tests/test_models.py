from app.models.approval_step import ApprovalStep, StepStatus
from app.models.audit_log import AuditLog
from app.models.task import Task, TaskStatus
from app.models.user import User


def test_user_model_columns():
    cols = [c.name for c in User.__table__.columns]
    assert "id" in cols
    assert "email" in cols
    assert "hashed_password" in cols
    assert "is_owner" in cols


def test_task_status_values():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.IN_PROGRESS == "in_progress"
    assert TaskStatus.APPROVED == "approved"
    assert TaskStatus.REJECTED == "rejected"


def test_approval_step_columns():
    cols = [c.name for c in ApprovalStep.__table__.columns]
    assert "step_number" in cols
    assert "agent_role" in cols
    assert "output" in cols
    assert "status" in cols


def test_audit_log_model_columns():
    cols = [c.name for c in AuditLog.__table__.columns]
    assert "action" in cols
    assert "resource" in cols
    assert "ip_address" in cols
