from datetime import datetime, timezone

from bson import ObjectId

from app.core.database import db


async def create_audit_log(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    entity_label: str,
    actor_user_id: str,
    actor_role: str,
    details: dict | None = None,
    session=None,
):
    """Write an audit entry, optionally in the caller's transaction."""
    entry = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_label": entity_label,
        "actor_user_id": ObjectId(actor_user_id),
        "actor_role": actor_role,
        "created_at": datetime.now(timezone.utc),
    }
    if details:
        entry["details"] = details

    result = await db.audit_logs.insert_one(entry, session=session)
    return str(result.inserted_id)
