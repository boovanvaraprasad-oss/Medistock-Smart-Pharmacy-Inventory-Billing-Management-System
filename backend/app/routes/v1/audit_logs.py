import re

from bson import ObjectId
from fastapi import APIRouter, Depends, Query

from app.core.database import db
from app.core.dependencies import require_permission
from app.core.permissions import AUDIT_LOG_READ


router = APIRouter(prefix="/audit-logs", tags=["Audit trail"])


@router.get("")
async def get_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    action: str | None = None,
    entity_type: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    current_user=Depends(require_permission(AUDIT_LOG_READ)),
):
    query = {}
    if action:
        query["action"] = action
    if entity_type:
        query["entity_type"] = entity_type
    if q and q.strip():
        pattern = re.escape(q.strip())
        matching_users = await db.users.find(
            {"email": {"$regex": pattern, "$options": "i"}},
            {"_id": 1},
        ).to_list(length=100)
        matching_suppliers = await db.suppliers.find(
            {"name": {"$regex": pattern, "$options": "i"}},
            {"_id": 1},
        ).to_list(length=100)
        searchable = [
            {field: {"$regex": pattern, "$options": "i"}}
            for field in (
                "action",
                "entity_type",
                "entity_label",
                "entity_id",
                "details.supplier_name",
                "details.medicine_name",
                "details.batch_number",
                "details.reason",
                "details.payment_method",
            )
        ]
        actor_ids = [user["_id"] for user in matching_users]
        if actor_ids:
            searchable.append({"actor_user_id": {"$in": actor_ids}})
        supplier_ids = [str(supplier["_id"]) for supplier in matching_suppliers]
        if supplier_ids:
            searchable.append({"details.supplier_id": {"$in": supplier_ids}})
        query["$or"] = searchable

    total = await db.audit_logs.count_documents(query)
    cursor = (
        db.audit_logs.find(query)
        .sort([("created_at", -1), ("_id", -1)])
        .skip((page - 1) * limit)
        .limit(limit)
    )
    records = await cursor.to_list(length=limit)
    actor_ids = list({record.get("actor_user_id") for record in records if isinstance(record.get("actor_user_id"), ObjectId)})
    users = await db.users.find({"_id": {"$in": actor_ids}}, {"email": 1, "full_name": 1, "name": 1}).to_list(length=limit) if actor_ids else []
    emails = {user["_id"]: user.get("email", "") for user in users}
    names = {user["_id"]: user.get("full_name") or user.get("name", "") for user in users}

    supplier_ids = set()
    for record in records:
        supplier_id = (record.get("details") or {}).get("supplier_id")
        if supplier_id:
            try:
                supplier_ids.add(ObjectId(supplier_id))
            except Exception:
                continue
    suppliers = await db.suppliers.find(
        {"_id": {"$in": list(supplier_ids)}},
        {"name": 1},
    ).to_list(length=limit) if supplier_ids else []
    supplier_names = {supplier["_id"]: supplier.get("name", "Unknown supplier") for supplier in suppliers}

    def audit_details(record):
        details = dict(record.get("details") or {})
        supplier_id = details.get("supplier_id")
        if supplier_id:
            try:
                supplier_name = supplier_names.get(ObjectId(supplier_id))
            except Exception:
                supplier_name = None
            if supplier_name:
                details["supplier_name"] = supplier_name
            details.pop("supplier_id", None)
        return details

    return {
        "items": [
            {
                "id": str(record["_id"]),
                "action": record.get("action", "Unknown"),
                "entity_type": record.get("entity_type", ""),
                "entity_id": record.get("entity_id", ""),
                "entity_label": record.get("entity_label", ""),
                "actor_user_id": str(record.get("actor_user_id", "")),
                "actor_email": emails.get(record.get("actor_user_id"), "Former or unknown user"),
                "actor_name": names.get(record.get("actor_user_id"), ""),
                "actor_role": record.get("actor_role", "Unknown"),
                "created_at": record.get("created_at"),
                "details": audit_details(record),
            }
            for record in records
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }
