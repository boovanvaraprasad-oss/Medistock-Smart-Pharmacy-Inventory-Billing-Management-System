from app.core.database import db


async def get_low_stock_medicines(
    threshold: int,
):
    medicines = []

    cursor = db.medicines.find(
        {
            "stock": {
                "$lte": threshold
            },
            "is_active": True,
        }
    ).sort(
        "stock",
        1,
    )

    async for medicine in cursor:
        medicines.append(
            {
                "id": str(medicine["_id"]),
                "name": medicine["name"],
                "stock": medicine.get(
                    "stock",
                    0,
                ),
                "threshold": threshold,
            }
        )

    return medicines