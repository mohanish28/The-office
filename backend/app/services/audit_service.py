from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    resource: str,
    user_id: str | None = None,
    detail: str | None = None,
    ip: str | None = None,
) -> None:
    entry = AuditLog(user_id=user_id, action=action, resource=resource, detail=detail, ip_address=ip)
    db.add(entry)
    await db.commit()
