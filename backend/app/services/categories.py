from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db


async def create_category(name: str):
    # checks the category if it already exists
    existing_category = await db.categories.find_one(
        {"name": name}
    )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists",
        )

    category = {
        "name": name,
        "is_active": True,
    }

    result = await db.categories.insert_one(category)

    return {
        "id": str(result.inserted_id),
        "name": name,
        "is_active": True,
    }


async def get_all_categories():
    categories = []

    cursor = db.categories.find(
        {}
    )

    async for category in cursor:
        categories.append({
            "id": str(category["_id"]),
            "name": category["name"],
            "is_active": category.get("is_active", True),
        })

    return categories


async def update_category(
    category_id: str,
    name: str | None = None,
    is_active: bool | None = None,
):
    # Validate the category ID
    try:
        object_id = ObjectId(category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID",
        )

    # Check whether the category exists
    category = await db.categories.find_one(
        {"_id": object_id}
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check for duplicate category name
    if name is not None:
        existing_category = await db.categories.find_one(
            {
                "name": name,
                "_id": {"$ne": object_id},
            }
        )

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A category with this name already exists",
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

    await db.categories.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    # Get the updated category
    updated_category = await db.categories.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated_category["_id"]),
        "name": updated_category["name"],
        "is_active": updated_category.get("is_active", True),
    }