OWNER = "owner"
PHARMACIST = "pharmacist"
INVENTORY_EXECUTIVE = "inventory_executive"
PURCHASE_EXECUTIVE = "purchase_executive"
STORE_MANAGER = "store_manager"
COMPLIANCE_OFFICER = "compliance_officer"


ROLES = [
    OWNER,
    PHARMACIST,
    INVENTORY_EXECUTIVE,
    PURCHASE_EXECUTIVE,
    STORE_MANAGER,
    COMPLIANCE_OFFICER,
]


USER_READ = "user:read"
USER_WRITE = "user:write"

MEDICINE_READ = "medicine:read"
MEDICINE_WRITE = "medicine:write"

STOCK_READ = "stock:read"
STOCK_WRITE = "stock:write"

SUPPLIER_READ = "supplier:read"
SUPPLIER_WRITE = "supplier:write"

PURCHASE_READ = "purchase:read"
PURCHASE_WRITE = "purchase:write"

BILL_CREATE = "bill:create"
BILL_READ = "bill:read"

REPORT_VIEW = "report:view"


PERMISSIONS = [
    USER_READ,
    USER_WRITE,
    MEDICINE_READ,
    MEDICINE_WRITE,
    STOCK_READ,
    STOCK_WRITE,
    SUPPLIER_READ,
    SUPPLIER_WRITE,
    PURCHASE_READ,
    PURCHASE_WRITE,
    BILL_CREATE,
    BILL_READ,
    REPORT_VIEW,
]


ROLE_PERMISSIONS = {
    OWNER: PERMISSIONS,

    PHARMACIST: [
        MEDICINE_READ,
        STOCK_READ,
        BILL_CREATE,
        BILL_READ,
    ],

    INVENTORY_EXECUTIVE: [
        MEDICINE_READ,
        MEDICINE_WRITE,
        STOCK_READ,
        STOCK_WRITE,
        SUPPLIER_READ,
    ],

    PURCHASE_EXECUTIVE: [
        MEDICINE_READ,
        STOCK_READ,
        SUPPLIER_READ,
        SUPPLIER_WRITE,
        PURCHASE_READ,
        PURCHASE_WRITE,
    ],

    STORE_MANAGER: [
        MEDICINE_READ,
        STOCK_READ,
        SUPPLIER_READ,
        PURCHASE_READ,
        BILL_READ,
        REPORT_VIEW,
    ],

    COMPLIANCE_OFFICER: [
        USER_READ,
        MEDICINE_READ,
        STOCK_READ,
        BILL_READ,
        REPORT_VIEW,
    ],
}