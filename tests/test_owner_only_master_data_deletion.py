import pytest
from fastapi.routing import APIRoute

from app.core.permissions import (
    MASTER_DATA_DELETE,
    OWNER,
    ROLE_PERMISSIONS,
    ROLES,
    USER_DELETE,
)
from main import app
from app.routes.v1.categories import router as categories_router
from app.routes.v1.manufacturers import router as manufacturers_router
from app.routes.v1.medicines import router as medicines_router
from app.routes.v1.suppliers import router as suppliers_router
from app.routes.v1.units import router as units_router
from app.routes.v1.users import router as users_router


DELETE_ROUTES = {
    "/api/v1/medicines/{medicine_id}": (
        medicines_router,
        "/{medicine_id}",
        MASTER_DATA_DELETE,
    ),
    "/api/v1/categories/{category_id}": (
        categories_router,
        "/{category_id}",
        MASTER_DATA_DELETE,
    ),
    "/api/v1/manufacturers/{manufacturer_id}": (
        manufacturers_router,
        "/{manufacturer_id}",
        MASTER_DATA_DELETE,
    ),
    "/api/v1/units/{unit_id}": (
        units_router,
        "/{unit_id}",
        MASTER_DATA_DELETE,
    ),
    "/api/v1/suppliers/{supplier_id}": (
        suppliers_router,
        "/{supplier_id}",
        MASTER_DATA_DELETE,
    ),
    "/api/v1/users/{user_id}": (users_router, "/{user_id}", USER_DELETE),
}


def get_delete_route(path):
    router, local_path, _ = DELETE_ROUTES[path]
    for route in router.routes:
        if (
            isinstance(route, APIRoute)
            and route.path == f"{router.prefix}{local_path}"
        ):
            if "DELETE" in route.methods:
                return route
    raise AssertionError(f"DELETE route not registered: {path}")


@pytest.mark.parametrize("path", sorted(DELETE_ROUTES))
def test_delete_routes_use_owner_only_permission(path):
    route = get_delete_route(path)
    checker = route.dependant.dependencies[0].call
    captured_permissions = {
        cell.cell_contents
        for cell in checker.__closure__ or []
        if isinstance(cell.cell_contents, str)
    }

    _, _, permission = DELETE_ROUTES[path]
    assert permission in captured_permissions
    assert permission in ROLE_PERMISSIONS[OWNER]
    assert all(
        permission not in ROLE_PERMISSIONS[role]
        for role in ROLES
        if role != OWNER
    )


@pytest.mark.parametrize("path", sorted(DELETE_ROUTES))
def test_delete_routes_are_published(path):
    assert "delete" in app.openapi()["paths"][path]
