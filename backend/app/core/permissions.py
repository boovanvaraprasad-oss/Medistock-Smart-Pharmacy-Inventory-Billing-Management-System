OWNER = "owner"
PHARMACIST = "pharmacist"
INVENTORY = "inventory"
PROCUREMENT = "procurement"
MANAGER = "manager"
AUDITOR = "auditor"


ROLES = [
    OWNER,
    PHARMACIST,
    INVENTORY,
    PROCUREMENT,
    MANAGER,
    AUDITOR,
]

USER_READ = "user:read"
USER_WRITE = "user:write"

MEDICINE_READ = "medicine:read"
MEDICINE_WRITE = "medicine:write"

STOCK_READ = "stock:read"
STOCK_WRITE = "stock:write"

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

    INVENTORY: [
        MEDICINE_READ,
        MEDICINE_WRITE,
        STOCK_READ,
        STOCK_WRITE,
    ],

    PROCUREMENT: [
        MEDICINE_READ,
        MEDICINE_WRITE,
        STOCK_READ,
    ],

    MANAGER: [
        MEDICINE_READ,
        STOCK_READ,
        BILL_READ,
        REPORT_VIEW,
    ],

    AUDITOR: [
        USER_READ,
        MEDICINE_READ,
        STOCK_READ,
        BILL_READ,
        REPORT_VIEW,
    ],
}