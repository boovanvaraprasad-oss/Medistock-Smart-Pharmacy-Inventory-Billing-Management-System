from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db
from app.services.name_utils import normalize_name


async def create_unit(name: str):
    name = normalize_name(name)

    existing_unit = await db.units.find_one(
        {"name": name}
    )

    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A unit with this name already exists",
        )

    unit = {
        "name": name,
        "is_active": True,
    }

    result = await db.units.insert_one(unit)

    return {
        "id": str(result.inserted_id),
        "name": name,
        "is_active": True,
    }


async def get_all_units():
    units = []

    cursor = db.units.find({})

    async for unit in cursor:
        units.append(
            {
                "id": str(unit["_id"]),
                "name": unit["name"],
                "is_active": unit.get(
                    "is_active",
                    True,
                ),
            }
        )

    return units


async def update_unit(
    unit_id: str,
    name: str | None = None,
    is_active: bool | None = None,
):
    try:
        object_id = ObjectId(unit_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid unit ID",
        )

    unit = await db.units.find_one(
        {"_id": object_id}
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    if name is not None:
        name = normalize_name(name)

        existing_unit = await db.units.find_one(
            {
                "name": name,
                "_id": {"$ne": object_id},
            }
        )

        if existing_unit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A unit with this name already exists",
            )

    # Prevent deactivation when an active medicine
    # is still using this unit.
    if is_active is False:
        active_medicine = await db.medicines.find_one(
            {
                "unit_id": object_id,
                "is_active": {"$ne": False},
            }
        )

        if active_medicine:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot deactivate unit because "
                    "an active medicine is using it"
                ),
            )

    update_data = {}

    if name is not None:
        update_data["name"] = name

    if is_active is not None:
        update_data["is_active"] = is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.units.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_unit = await db.units.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated_unit["_id"]),
        "name": updated_unit["name"],
        "is_active": updated_unit.get(
            "is_active",
            True,
        ),
    }