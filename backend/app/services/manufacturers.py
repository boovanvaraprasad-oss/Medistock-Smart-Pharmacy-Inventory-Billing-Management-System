from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db


async def create_manufacturer(name: str):
    # Check whether the manufacturer already exists
    existing_manufacturer = await db.manufacturers.find_one(
        {"name": name}
    )

    if existing_manufacturer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A manufacturer with this name already exists",
        )

    manufacturer = {
        "name": name,
        "is_active": True,
    }

    result = await db.manufacturers.insert_one(manufacturer)

    return {
        "id": str(result.inserted_id),
        "name": name,
        "is_active": True,
    }


async def get_all_manufacturers():
    manufacturers = []

    cursor = db.manufacturers.find({})

    async for manufacturer in cursor:
        manufacturers.append({
            "id": str(manufacturer["_id"]),
            "name": manufacturer["name"],
            "is_active": manufacturer.get("is_active", True),
        })

    return manufacturers


async def update_manufacturer(
    manufacturer_id: str,
    name: str | None = None,
    is_active: bool | None = None,
):
    # Validate the manufacturer ID
    try:
        object_id = ObjectId(manufacturer_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid manufacturer ID",
        )

    # Check whether the manufacturer exists
    manufacturer = await db.manufacturers.find_one(
        {"_id": object_id}
    )

    if not manufacturer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found",
        )

    # Check for duplicate manufacturer name
    if name is not None:
        existing_manufacturer = await db.manufacturers.find_one(
            {
                "name": name,
                "_id": {"$ne": object_id},
            }
        )

        if existing_manufacturer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A manufacturer with this name already exists",
            )

    # Fields to update
    update_data = {}

    if name is not None:
        update_data["name"] = name

    if is_active is not None:
        update_data["is_active"] = is_active

    # Nothing was provided to update
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.manufacturers.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    # Get the updated manufacturer
    updated_manufacturer = await db.manufacturers.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated_manufacturer["_id"]),
        "name": updated_manufacturer["name"],
        "is_active": updated_manufacturer.get("is_active", True),
    }