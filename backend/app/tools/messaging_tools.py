from __future__ import annotations

import uuid
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import SupplierMessage


async def send_supplier_message(
    session: AsyncSession,
    supplier_id: str,
    subject: str,
    body: str,
    direction: str = "outbound",
) -> dict[str, Any]:
    """Send or log a communication with an external supplier."""
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    msg = SupplierMessage(
        message_id=msg_id,
        supplier_id=supplier_id,
        direction=direction,
        subject=subject,
        body=body,
        sent_at=now,
        responded_at=None,
    )
    session.add(msg)
    await session.flush()
    return {
        "message_id": msg_id,
        "supplier_id": supplier_id,
        "subject": subject,
        "sent_at": now.isoformat(),
        "direction": direction,
    }


async def simulate_supplier_response(
    session: AsyncSession,
    message_id: str,
    reply_body: str,
) -> dict[str, Any]:
    """Record an incoming simulated supplier response to an outbound message."""
    result = await session.execute(
        select(SupplierMessage).where(SupplierMessage.message_id == message_id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise ValueError(f"Message {message_id} not found")

    now = datetime.now(timezone.utc)
    msg.responded_at = now

    reply_id = str(uuid.uuid4())
    reply = SupplierMessage(
        message_id=reply_id,
        supplier_id=msg.supplier_id,
        direction="inbound",
        subject=f"Re: {msg.subject}",
        body=reply_body,
        sent_at=now,
        responded_at=now,
    )
    session.add(reply)
    await session.flush()

    return {
        "reply_id": reply_id,
        "original_message_id": message_id,
        "supplier_id": msg.supplier_id,
        "responded_at": now.isoformat(),
    }
