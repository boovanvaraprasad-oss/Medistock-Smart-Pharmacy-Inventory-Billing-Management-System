const homeTiles = document.getElementById("homeTiles");
const homeError = document.getElementById("homeError");
const homeTileCount = document.getElementById("tileCount");
const logoutButton = document.getElementById("logoutButton");

const roleDetails = {
    owner: {
        label: "Owner access",
        description: "You have full pharmacy access. Choose where you want to go."
    },
    pharmacist: {
        label: "Pharmacist access",
        description: "Look up medicines and stock, create bills, and manage customer returns."
    },
    inventory_executive: {
        label: "Inventory executive access",
        description: "Maintain the medicine catalogue, track batches and expiry, and view suppliers."
    },
    purchase_executive: {
        label: "Purchase executive access",
        description: "Coordinate suppliers and purchase orders with clear stock visibility."
    },
    store_manager: {
        label: "Store manager access",
        description: "Oversee store operations, billing, purchasing, reports and login activity."
    },
    compliance_officer: {
        label: "Compliance officer access",
        description: "Review staff, inventory, billing records, reports and the audit trail."
    }
};

const tileDefinitions = [
    {
        title: "Overview",
        description: "Your role dashboard and pharmacy activity.",
        href: (user) => getDashboardForRole(user.role),
        icon: "overview"
    },
    {
        title: "Medicines",
        description: "Browse and manage medicine records.",
        writeDescription: "Add and manage medicine records.",
        href: "medicines.html",
        permissions: ["medicine:read", "medicine:write"],
        writePermission: "medicine:write",
        icon: "medicine"
    },
    {
        title: "Stock and batches",
        description: "Review quantities, batches and expiry dates.",
        href: "batches.html",
        permissions: ["stock:read"],
        icon: "stock"
    },
    {
        title: "Categories",
        description: "Browse and organize medicine categories.",
        href: "categories.html",
        permissions: ["medicine:read", "medicine:write"],
        icon: "categories"
    },
    {
        title: "Manufacturers",
        description: "View medicine manufacturers.",
        href: "manufacturers.html",
        permissions: ["medicine:read", "medicine:write"],
        icon: "manufacturers"
    },
    {
        title: "Units",
        description: "View medicine units and packaging types.",
        href: "units.html",
        permissions: ["medicine:read", "medicine:write"],
        icon: "units"
    },
    {
        title: "Billing and returns",
        description: "Review billing records.",
        writeDescription: "Create bills and process customer returns.",
        href: "billing.html",
        permissions: ["bill:read", "bill:create"],
        writePermission: "bill:create",
        icon: "billing"
    },
    {
        title: "Suppliers",
        description: "View supplier records.",
        writeDescription: "Add and manage supplier records.",
        href: "suppliers.html",
        permissions: ["supplier:read", "supplier:write"],
        writePermission: "supplier:write",
        icon: "suppliers"
    },
    {
        title: "Purchase orders",
        description: "Review incoming stock and order status.",
        writeDescription: "Create and manage purchase orders.",
        href: "purchase_orders.html",
        permissions: ["purchase:read", "purchase:write"],
        writePermission: "purchase:write",
        icon: "purchases"
    },
    {
        title: "Notifications",
        description: "See stock and purchasing items that need attention.",
        href: "notifications.html",
        permissions: ["stock:read"],
        icon: "notifications"
    },
    {
        title: "Reports",
        description: "Review sales and stock reports.",
        href: "reports.html",
        permissions: ["report:view"],
        icon: "reports"
    },
    {
        title: "Staff and users",
        description: "Review staff accounts and assigned roles.",
        writeDescription: "Manage staff accounts and their roles.",
        href: "users.html",
        permissions: ["user:read", "user:write"],
        writePermission: "user:write",
        icon: "staff"
    },
    {
        title: "Login history",
        description: "Review account sign-in activity.",
        href: "login_history.html",
        roles: ["owner", "store_manager"],
        icon: "history"
    },
    {
        title: "Audit trail",
        description: "Review recorded changes across the pharmacy system.",
        href: "audit_trail.html",
        permissions: ["audit_log:read"],
        icon: "audit"
    },
    {
        title: "Settings",
        description: "Manage pharmacy and system preferences.",
        href: "settings.html",
        icon: "settings"
    }
];

const iconMarkup = {
    overview: '<rect x="3" y="3" width="7" height="8" rx="1"></rect><rect x="14" y="3" width="7" height="5" rx="1"></rect><rect x="14" y="12" width="7" height="9" rx="1"></rect><rect x="3" y="15" width="7" height="6" rx="1"></rect>',
    medicine: '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path><path d="m8.5 8.5 7 7"></path>',
    stock: '<path d="m12 3 9 5-9 5-9-5 9-5Z"></path><path d="M3 8v8l9 5 9-5V8M12 13v8"></path>',
    categories: '<rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect>',
    manufacturers: '<path d="M3 21V8l6 3V8l6 3V4h5v17Z"></path><path d="M7 21v-4h4v4m3 0v-4h4v4"></path>',
    units: '<path d="m3 17 14-14 4 4L7 21H3v-4Z"></path><path d="m13 7 4 4m-7-1 2 2m-5 1 2 2"></path>',
    billing: '<path d="M5 3h14v18l-3-2-3 2-3-2-3 2-2-2V3Z"></path><path d="M9 8h6m-6 4h6m-6 4h4"></path>',
    suppliers: '<path d="M3 7h11v11H3zM14 11h4l3 3v4h-7"></path><circle cx="7" cy="19" r="2"></circle><circle cx="18" cy="19" r="2"></circle>',
    purchases: '<path d="M3 4h2l2.5 11h10L20 8H6"></path><circle cx="10" cy="19" r="1.5"></circle><circle cx="17" cy="19" r="1.5"></circle>',
    notifications: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"></path>',
    reports: '<path d="M3 3v18h18"></path><path d="M8 15v-4m5 4V6m5 9V9"></path>',
    staff: '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="10" cy="7" r="4"></circle><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>',
    history: '<path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"></path><path d="M3 3v5h5m4-1v5l3 2"></path>',
    audit: '<path d="M8 3h8l4 4v14H4V3h4Z"></path><path d="M8 11h8m-8 4h8m-8 4h5M16 3v5h5"></path>',
    settings: '<circle cx="12" cy="12" r="3"></circle><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.8 1l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.8-1l-1.7.6-1.4-2.4 1.4-1.1a8 8 0 0 1 0-2l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.8-1l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.8 1l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1-.1 2Z"></path>'
};

function roleLabel(role) {
    return (role || "team member").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function canSeeTile(tile, user) {
    const permissions = user.permissions || [];
    if (tile.roles && !tile.roles.includes(user.role)) return false;
    return !tile.permissions || tile.permissions.some((permission) => permissions.includes(permission));
}

function createHomeTile(tile, user) {
    const link = document.createElement("a");
    link.className = "home-tile";
    link.href = typeof tile.href === "function" ? tile.href(user) : tile.href;

    const icon = document.createElement("span");
    icon.className = "home-tile-icon";
    icon.setAttribute("aria-hidden", "true");
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("focusable", "false");
    svg.innerHTML = iconMarkup[tile.icon] || "";
    icon.append(svg);

    const title = document.createElement("span");
    title.className = "home-tile-title";
    title.textContent = tile.title;

    const description = document.createElement("span");
    description.className = "home-tile-description";
    description.textContent = tile.writePermission && (user.permissions || []).includes(tile.writePermission)
        ? tile.writeDescription
        : tile.description;

    const arrow = document.createElement("span");
    arrow.className = "home-tile-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "→";

    link.append(icon, title, description, arrow);
    return link;
}

function renderHome(user) {
    const details = roleDetails[user.role] || {
        label: "Team access",
        description: "Choose an area available to your account."
    };
    const name = user.name || user.full_name || user.email || "there";
    const allowedTiles = tileDefinitions.filter((tile) => canSeeTile(tile, user));

    document.getElementById("homeUser").textContent = `${name} · ${roleLabel(user.role)}`;
    document.getElementById("welcomeName").textContent = name;
    document.getElementById("roleLabel").textContent = details.label;
    document.getElementById("roleDescription").textContent = details.description;
    homeTiles.replaceChildren(...allowedTiles.map((tile) => createHomeTile(tile, user)));
    homeTileCount.textContent = `${allowedTiles.length} areas available to your role`;
}

async function initializeHome() {
    if (!localStorage.getItem("access_token")) {
        window.location.replace("/");
        return;
    }

    try {
        const currentUser = await getCurrentUser();
        renderHome(currentUser);
    } catch {
        homeError.hidden = false;
        homeError.textContent = "Your session could not be verified. Please sign in again.";
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        sessionStorage.removeItem("medistock_current_user");
        window.setTimeout(() => window.location.replace("/login.html"), 900);
    }
}

logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;
    logoutButton.textContent = "Logging out…";
    try {
        await logoutUser();
    } catch {
        // Remove the local session even if the server is unavailable.
    } finally {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        sessionStorage.removeItem("medistock_current_user");
        window.location.replace("/");
    }
});

initializeHome();
