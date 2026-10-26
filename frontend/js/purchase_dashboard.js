const purchaseStatusMessage = document.getElementById("statusMessage");
const purchaseErrorMessage = document.getElementById("errorMessage");
const purchaseDashboardContent = document.getElementById("dashboardContent");
const purchaseRefreshButton = document.getElementById("refreshButton");
const purchaseOrderRows = document.getElementById("purchaseOrderRows");
const ordersEmpty = document.getElementById("ordersEmpty");
const supplierList = document.getElementById("supplierList");
const suppliersEmpty = document.getElementById("suppliersEmpty");

const purchaseNumberFormatter = new Intl.NumberFormat("en-IN");
const purchaseCurrencyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
});

function setPurchaseMetric(id, value) {
    document.getElementById(id).textContent = value;
}

function appendPurchaseCell(row, value, className) {
    const cell = document.createElement("td");
    cell.textContent = value;
    if (className) cell.className = className;
    row.appendChild(cell);
    return cell;
}

function renderPurchaseOrders(orders, suppliers, items) {
    const activeOrders = orders.filter((order) => order.is_active !== false);
    const supplierById = new Map(suppliers.map((supplier) => [supplier.id, supplier]));
    const itemSummary = new Map();

    for (const item of items) {
        const current = itemSummary.get(item.purchase_order_id) || { count: 0, total: 0 };
        current.count += 1;
        current.total += Number(item.total_price || 0);
        itemSummary.set(item.purchase_order_id, current);
    }

    const orderedForDisplay = [...activeOrders].sort((left, right) => {
        const priority = { draft: 0, ordered: 1, received: 2, cancelled: 3 };
        return (priority[left.status] ?? 4) - (priority[right.status] ?? 4);
    });

    purchaseOrderRows.replaceChildren();
    ordersEmpty.hidden = orderedForDisplay.length > 0;

    for (const order of orderedForDisplay.slice(0, 10)) {
        const row = document.createElement("tr");
        const supplier = supplierById.get(order.supplier_id);
        appendPurchaseCell(row, supplier?.name || "Unknown supplier");

        const statusCell = document.createElement("td");
        const status = document.createElement("span");
        status.className = "purchase-status";
        status.dataset.status = order.status || "draft";
        status.textContent = (order.status || "draft").replaceAll("_", " ");
        statusCell.appendChild(status);
        row.appendChild(statusCell);

        const summary = itemSummary.get(order.id) || { count: 0, total: 0 };
        appendPurchaseCell(row, purchaseNumberFormatter.format(summary.count));
        appendPurchaseCell(row, purchaseCurrencyFormatter.format(summary.total), "purchase-value");

        const noteCell = appendPurchaseCell(row, order.notes || "—");
        if (order.notes) {
            noteCell.className = "purchase-note";
            noteCell.title = order.notes;
        }
        purchaseOrderRows.appendChild(row);
    }
}

function renderSuppliers(suppliers) {
    const activeSuppliers = suppliers.filter((supplier) => supplier.is_active !== false);
    supplierList.replaceChildren();
    suppliersEmpty.hidden = activeSuppliers.length > 0;

    for (const supplier of activeSuppliers.slice(0, 6)) {
        const row = document.createElement("article");
        row.className = "supplier-entry";

        const avatar = document.createElement("span");
        avatar.className = "supplier-avatar";
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = (supplier.name || "S").trim().charAt(0).toUpperCase();

        const copy = document.createElement("span");
        copy.className = "supplier-copy";
        const name = document.createElement("strong");
        name.textContent = supplier.name || "Unnamed supplier";
        const contact = document.createElement("small");
        contact.textContent = supplier.phone || supplier.email || "No contact details";
        copy.append(name, contact);

        row.append(avatar, copy);
        supplierList.appendChild(row);
    }
}

async function loadPurchaseDashboard() {
    purchaseStatusMessage.textContent = "Loading purchasing overview…";
    purchaseStatusMessage.hidden = false;
    purchaseErrorMessage.hidden = true;
    purchaseDashboardContent.hidden = true;
    purchaseRefreshButton.disabled = true;

    try {
        const currentUser = await getCurrentUser();
        const destination = getDashboardForRole(currentUser.role);
        if (destination !== "purchase_dashboard.html") {
            window.location.replace(destination);
            return;
        }

        const [orders, suppliers, items] = await Promise.all([
            apiRequest("/api/v1/purchase-orders"),
            apiRequest("/api/v1/suppliers"),
            apiRequest("/api/v1/purchase-items")
        ]);

        const activeOrders = orders.filter((order) => order.is_active !== false);
        const drafts = activeOrders.filter((order) => order.status === "draft");
        const ordered = activeOrders.filter((order) => order.status === "ordered");
        const open = activeOrders.filter((order) => ["draft", "ordered"].includes(order.status));
        const activeSuppliers = suppliers.filter((supplier) => supplier.is_active !== false);

        setPurchaseMetric("openOrderCount", purchaseNumberFormatter.format(open.length));
        setPurchaseMetric("draftOrderCount", purchaseNumberFormatter.format(drafts.length));
        setPurchaseMetric("orderedCount", purchaseNumberFormatter.format(ordered.length));
        setPurchaseMetric("supplierCount", purchaseNumberFormatter.format(activeSuppliers.length));

        renderPurchaseOrders(orders, suppliers, items);
        renderSuppliers(suppliers);

        purchaseStatusMessage.hidden = true;
        purchaseDashboardContent.hidden = false;
    } catch (error) {
        purchaseStatusMessage.hidden = true;
        purchaseErrorMessage.textContent = error.message || "Unable to load the purchasing dashboard.";
        purchaseErrorMessage.hidden = false;

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    } finally {
        purchaseRefreshButton.disabled = false;
    }
}

purchaseRefreshButton.addEventListener("click", loadPurchaseDashboard);
loadPurchaseDashboard();
