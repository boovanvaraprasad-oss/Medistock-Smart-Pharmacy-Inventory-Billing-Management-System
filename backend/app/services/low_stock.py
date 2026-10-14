from app.core.database import db


async def get_low_stock_medicines():
    medicines = []

    cursor = db.medicines.find(
        {
            "is_active": True,
        }
    ).sort(
        "stock",
        1,
    )

    async for medicine in cursor:
        stock = medicine.get("stock", 0)
        reorder_threshold = medicine.get("reorder_threshold", 10)

        if stock <= reorder_threshold:
            medicines.append(
                {
                    "id": str(medicine["_id"]),
                    "name": medicine["name"],
                    "stock": stock,
                    "threshold": reorder_threshold,
                }
            )

    return medicines