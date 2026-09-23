from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db


async def create_medicine(
    name: str,
    category_id: str,
    manufacturer_id: str,
    unit_id: str,
    supplier_id: str,
):
    # Check whether medicine already exists
    existing_medicine = await db.medicines.find_one(
        {"name": name}
    )

    if existing_medicine:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A medicine with this name already exists",
        )

    # Validate referenced master data
    references = [
        ("category", "categories", category_id),
        ("manufacturer", "manufacturers", manufacturer_id),
        ("unit", "units", unit_id),
        ("supplier", "suppliers", supplier_id),
    ]

    reference_ids = {}

    for field_name, collection_name, reference_id in references:
        try:
            object_id = ObjectId(reference_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} ID",
            )

        document = await db[collection_name].find_one(
            {
                "_id": object_id,
                "is_active": True,
            }
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name.capitalize()} not found or inactive",
            )

        reference_ids[f"{field_name}_id"] = object_id

    medicine = {
        "name": name,
        "category_id": reference_ids["category_id"],
        "manufacturer_id": reference_ids["manufacturer_id"],
        "unit_id": reference_ids["unit_id"],
        "supplier_id": reference_ids["supplier_id"],
        "is_active": True,
    }

    result = await db.medicines.insert_one(medicine)

    return {
        "id": str(result.inserted_id),
        "name": name,
        "category_id": category_id,
        "manufacturer_id": manufacturer_id,
        "unit_id": unit_id,
        "supplier_id": supplier_id,
        "is_active": True,
    }


async def get_all_medicines():
    medicines = []

    cursor = db.medicines.find({})

    async for medicine in cursor:
        medicines.append({
            "id": str(medicine["_id"]),
            "name": medicine["name"],
            "category_id": str(medicine["category_id"]),
            "manufacturer_id": str(medicine["manufacturer_id"]),
            "unit_id": str(medicine["unit_id"]),
            "supplier_id": str(medicine["supplier_id"]),
            "is_active": medicine.get("is_active", True),
        })

    return medicines


async def update_medicine(
    medicine_id: str,
    name: str | None = None,
    category_id: str | None = None,
    manufacturer_id: str | None = None,
    unit_id: str | None = None,
    supplier_id: str | None = None,
    is_active: bool | None = None,
):
    try:
        object_id = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid medicine ID",
        )

    medicine = await db.medicines.find_one(
        {"_id": object_id}
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    # Check duplicate medicine name
    if name is not None:
        existing_medicine = await db.medicines.find_one(
            {
                "name": name,
                "_id": {"$ne": object_id},
            }
        )

        if existing_medicine:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A medicine with this name already exists",
            )

    update_data = {}

    if name is not None:
        update_data["name"] = name

    # Validate and update referenced master data
    references = [
        ("category_id", "categories", category_id),
        ("manufacturer_id", "manufacturers", manufacturer_id),
        ("unit_id", "units", unit_id),
        ("supplier_id", "suppliers", supplier_id),
    ]

    for field_name, collection_name, reference_id in references:
        if reference_id is not None:
            try:
                reference_object_id = ObjectId(reference_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name.replace('_id', '')} ID",
                )

            document = await db[collection_name].find_one(
                {
                    "_id": reference_object_id,
                    "is_active": True,
                }
            )

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"{field_name.replace('_id', '').capitalize()} "
                        "not found or inactive"
                    ),
                )

            update_data[field_name] = reference_object_id

    if is_active is not None:
        update_data["is_active"] = is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.medicines.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_medicine = await db.medicines.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated_medicine["_id"]),
        "name": updated_medicine["name"],
        "category_id": str(updated_medicine["category_id"]),
        "manufacturer_id": str(updated_medicine["manufacturer_id"]),
        "unit_id": str(updated_medicine["unit_id"]),
        "supplier_id": str(updated_medicine["supplier_id"]),
        "is_active": updated_medicine.get("is_active", True),
    }