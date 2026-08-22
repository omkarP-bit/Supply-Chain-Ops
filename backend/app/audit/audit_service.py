from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.audit_repo import create_audit_event


async def log_event(
    session: AsyncSession,
    incident_id: str,
    agent_name: str,
    event_type: str,
    action: str,
    input_data: dict | None = None,
    output_data: dict | None = None,
    reason: str | None = None,
    risk_level: str | None = None,
    correlation_id: str | None = None,
) -> None:
    await create_audit_event(
        session,
        incident_id=incident_id,
        agent_name=agent_name,
        event_type=event_type,
        action=action,
        input_data=input_data,
        output_data=output_data,
        reason=reason,
        risk_level=risk_level,
        correlation_id=correlation_id,
    )
