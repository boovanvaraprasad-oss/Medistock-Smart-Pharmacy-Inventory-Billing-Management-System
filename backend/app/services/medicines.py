import re
from datetime import datetime, timezone

from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db


def to_object_id(value: str, label: str) -> ObjectId:
    # Turns the text ID into a MongoDB ID,
    # or answers 400 if the text is not a valid ID.
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {label} ID",
        )


def to_medicine_response(medicine: dict) -> dict:
    return {
        "id": str(medicine["_id"]),
        "name": medicine["name"],
        "sku": medicine.get("sku"),
        "dosage_form": medicine.get("dosage_form"),
        "category_id": str(medicine["category_id"]),
        "manufacturer_id": str(medicine["manufacturer_id"]),
        "unit_id": str(medicine["unit_id"]),
        "supplier_id": str(medicine["supplier_id"]),
        "stock": medicine.get("stock", 0),
        "price": medicine.get("price", 0),
        "reorder_threshold": medicine.get("reorder_threshold", 10),
        "is_controlled_substance": medicine.get(
            "is_controlled_substance",
            False,
        ),
        "is_active": medicine.get("is_active", True),
        "created_at": medicine.get("created_at"),
        "updated_at": medicine.get("updated_at"),
    }


async def create_medicine(
    name: str,
    sku: str,
    dosage_form: str,
    category_id: str,
    manufacturer_id: str,
    unit_id: str,
    supplier_id: str,
    price: float = 0,
    reorder_threshold: int = 10,
    is_controlled_substance: bool = False,
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

    # Check whether the SKU is already used
    existing_sku = await db.medicines.find_one(
        {"sku": sku}
    )

    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A medicine with this SKU already exists",
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
                detail=(
                    f"{field_name.capitalize()} "
                    "not found or inactive"
                ),
            )

        reference_ids[
            f"{field_name}_id"
        ] = object_id

    now = datetime.now(timezone.utc)

    medicine = {
        "name": name,
        "sku": sku,
        "dosage_form": dosage_form,
        "category_id": reference_ids["category_id"],
        "manufacturer_id": reference_ids["manufacturer_id"],
        "unit_id": reference_ids["unit_id"],
        "supplier_id": reference_ids["supplier_id"],
        # New medicines start with no stock.
        # Stock only arrives through a purchase order receipt.
        "stock": 0,
        "price": price,
        "reorder_threshold": reorder_threshold,
        "is_controlled_substance": is_controlled_substance,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.medicines.insert_one(
        medicine
    )

    medicine["_id"] = result.inserted_id

    return to_medicine_response(medicine)


async def list_medicines(
    search: str | None = None,
    category_id: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    limit: int = 20,
):
    # Build the search conditions from whatever filters were given
    query = {}

    if search and search.strip():
        # re.escape makes special characters like ( or . plain text
        query["name"] = {
            "$regex": re.escape(search.strip()),
            "$options": "i",
        }

    if category_id is not None:
        query["category_id"] = to_object_id(
            category_id,
            "category",
        )

    if is_active is True:
        # Older records may have no is_active field,
        # and those count as active
        query["is_active"] = {"$ne": False}
    elif is_active is False:
        query["is_active"] = False

    total = await db.medicines.count_documents(query)

    cursor = (
        db.medicines.find(query)
        .sort("name", 1)
        .skip((page - 1) * limit)
        .limit(limit)
    )

    items = []

    async for medicine in cursor:
        items.append(to_medicine_response(medicine))

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


async def get_medicine(medicine_id: str):
    object_id = to_object_id(medicine_id, "medicine")

    medicine = await db.medicines.find_one(
        {"_id": object_id}
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    return to_medicine_response(medicine)


async def update_medicine(
    medicine_id: str,
    name: str | None = None,
    sku: str | None = None,
    dosage_form: str | None = None,
    category_id: str | None = None,
    manufacturer_id: str | None = None,
    unit_id: str | None = None,
    supplier_id: str | None = None,
    price: float | None = None,
    reorder_threshold: int | None = None,
    is_controlled_substance: bool | None = None,
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
                detail=(
                    "A medicine with this name "
                    "already exists"
                ),
            )

    # Check duplicate SKU
    if sku is not None:
        existing_sku = await db.medicines.find_one(
            {
                "sku": sku,
                "_id": {"$ne": object_id},
            }
        )

        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A medicine with this SKU "
                    "already exists"
                ),
            )

    update_data = {}

    if name is not None:
        update_data["name"] = name

    if sku is not None:
        update_data["sku"] = sku

    if dosage_form is not None:
        update_data["dosage_form"] = dosage_form

    if reorder_threshold is not None:
        update_data["reorder_threshold"] = reorder_threshold

    if is_controlled_substance is not None:
        update_data["is_controlled_substance"] = (
            is_controlled_substance
        )

    # Update price
    if price is not None:
        update_data["price"] = price

    # Validate and update referenced master data
    references = [
        (
            "category_id",
            "categories",
            category_id,
        ),
        (
            "manufacturer_id",
            "manufacturers",
            manufacturer_id,
        ),
        (
            "unit_id",
            "units",
            unit_id,
        ),
        (
            "supplier_id",
            "suppliers",
            supplier_id,
        ),
    ]

    for field_name, collection_name, reference_id in references:
        if reference_id is not None:
            try:
                reference_object_id = ObjectId(
                    reference_id
                )

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Invalid "
                        f"{field_name.replace('_id', '')} ID"
                    ),
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

            update_data[
                field_name
            ] = reference_object_id

    if is_active is not None:
        update_data["is_active"] = is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # Remember when this medicine was last changed
    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.medicines.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_medicine = await db.medicines.find_one(
        {"_id": object_id}
    )

    return to_medicine_response(updated_medicine)