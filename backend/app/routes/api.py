from fastapi import APIRouter

from app.routes.v1.health import router as health_router
from app.routes.v1.auth import router as auth_router
from app.routes.v1.users import router as users_router
from app.routes.v1.categories import router as categories_router
from app.routes.v1.manufacturers import router as manufacturers_router
from app.routes.v1.units import router as units_router
from app.routes.v1.suppliers import router as suppliers_router
from app.routes.v1.medicines import router as medicines_router
from app.routes.v1.purchase_orders import (
    router as purchase_orders_router,
)
from app.routes.v1.purchase_items import (
    router as purchase_items_router,
)
from app.routes.v1.stock import router as stock_router
from app.routes.v1.stock_batches import (
    router as stock_batches_router,
)
from app.routes.v1.bills import router as bills_router


api_router = APIRouter()


api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(categories_router)
api_router.include_router(manufacturers_router)
api_router.include_router(units_router)
api_router.include_router(suppliers_router)
api_router.include_router(medicines_router)
api_router.include_router(purchase_orders_router)
api_router.include_router(purchase_items_router)
api_router.include_router(stock_router)
api_router.include_router(stock_batches_router)
api_router.include_router(bills_router)