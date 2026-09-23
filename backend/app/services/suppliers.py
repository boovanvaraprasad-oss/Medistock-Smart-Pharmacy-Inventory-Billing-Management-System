from bson import ObjectId

from fastapi import HTTPException, status

from app.core.database import db


async def create_supplier(
    name: str,
    phone: str,
    email: str | None = None,
    address: str | None = None,
):
    # Check whether the supplier already exists
    existing_supplier = await db.suppliers.find_one(
        {"name": name}
    )

    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A supplier with this name already exists",
        )

    supplier = {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "is_active": True,
    }

    result = await db.suppliers.insert_one(supplier)

    return {
        "id": str(result.inserted_id),
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "is_active": True,
    }


async def get_all_suppliers():
    suppliers = []

    cursor = db.suppliers.find({})

    async for supplier in cursor:
        suppliers.append({
            "id": str(supplier["_id"]),
            "name": supplier["name"],
            "phone": supplier["phone"],
            "email": supplier.get("email"),
            "address": supplier.get("address"),
            "is_active": supplier.get("is_active", True),
        })

    return suppliers


async def update_supplier(
    supplier_id: str,
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    is_active: bool | None = None,
):
    try:
        object_id = ObjectId(supplier_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid supplier ID",
        )

    supplier = await db.suppliers.find_one(
        {"_id": object_id}
    )

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check duplicate supplier name
    if name is not None:
        existing_supplier = await db.suppliers.find_one(
            {
                "name": name,
                "_id": {"$ne": object_id},
            }
        )

        if existing_supplier:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A supplier with this name already exists",
            )

    update_data = {}

    if name is not None:
        update_data["name"] = name

    if phone is not None:
        update_data["phone"] = phone

    if email is not None:
        update_data["email"] = email

    if address is not None:
        update_data["address"] = address

    if is_active is not None:
        update_data["is_active"] = is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    await db.suppliers.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_supplier = await db.suppliers.find_one(
        {"_id": object_id}
    )

    return {
        "id": str(updated_supplier["_id"]),
        "name": updated_supplier["name"],
        "phone": updated_supplier["phone"],
        "email": updated_supplier.get("email"),
        "address": updated_supplier.get("address"),
        "is_active": updated_supplier.get("is_active", True),
    }