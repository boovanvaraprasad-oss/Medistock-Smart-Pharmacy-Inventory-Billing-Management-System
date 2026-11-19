const statusMessage = document.getElementById("statusMessage");
const errorMessage = document.getElementById("errorMessage");
const dashboardContent = document.getElementById("dashboardContent");
const refreshButton = document.getElementById("refreshButton");
const lowStockRows = document.getElementById("lowStockRows");
const lowStockEmpty = document.getElementById("lowStockEmpty");
const batchAlerts = document.getElementById("batchAlerts");
const batchAlertsEmpty = document.getElementById("batchAlertsEmpty");

const numberFormatter = new Intl.NumberFormat("en-IN");
const dateFormatter = new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric"
});

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

function appendCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.appendChild(cell);
}

async function loadAllActiveMedicines() {
    const pageSize = 100;
    const firstPage = await apiRequest(
        `/api/v1/medicines?page=1&limit=${pageSize}&is_active=true`
    );
    const pageCount = Math.ceil(firstPage.total / pageSize);
    const remainingPages = await Promise.all(
        Array.from({ length: Math.max(pageCount - 1, 0) }, (_, index) =>
            apiRequest(`/api/v1/medicines?page=${index + 2}&limit=${pageSize}&is_active=true`)
        )
    );

    return [firstPage, ...remainingPages].flatMap((page) => page.items);
}

function renderLowStock(medicines) {
    const lowStock = medicines
        .filter((medicine) =>
            Number(medicine.stock ?? 0) <= Number(medicine.reorder_threshold ?? 10)
        )
        .sort((left, right) => Number(left.stock ?? 0) - Number(right.stock ?? 0))
        .slice(0, 8);

    lowStockRows.replaceChildren();
    lowStockEmpty.hidden = lowStock.length > 0;

    for (const medicine of lowStock) {
        const row = document.createElement("tr");
        appendCell(row, medicine.name || "—");
        appendCell(row, medicine.sku || "—");
        appendCell(row, numberFormatter.format(medicine.stock ?? 0));
        appendCell(row, numberFormatter.format(medicine.reorder_threshold ?? 10));
        lowStockRows.appendChild(row);
    }
}

function renderBatchAlerts(alertResponse) {
    const alerts = alertResponse.items || [];
    batchAlerts.replaceChildren();
    batchAlertsEmpty.hidden = alerts.length > 0;

    for (const alert of alerts.slice(0, 8)) {
        const row = document.createElement("article");
        row.className = "batch-alert";
        row.dataset.status = alert.alert_status;

        const icon = document.createElement("span");
        icon.className = "batch-alert-icon";
        icon.textContent = alert.alert_status === "expired" ? "!" : "◷";

        const copy = document.createElement("span");
        copy.className = "batch-alert-copy";
        const name = document.createElement("strong");
        name.textContent = alert.medicine_name || "Unknown medicine";
        const details = document.createElement("small");
        const expiryDate = alert.expiry_date
            ? dateFormatter.format(new Date(`${alert.expiry_date}T00:00:00`))
            : "Expiry date unavailable";
        details.textContent = `Batch ${alert.batch_number || "—"} · ${
            alert.alert_status === "expired" ? "Expired" : `Expires ${expiryDate}`
        }`;
        copy.append(name, details);

        const quantity = document.createElement("strong");
        quantity.className = "batch-alert-quantity";
        quantity.textContent = `${numberFormatter.format(alert.quantity ?? 0)} units`;

        row.append(icon, copy, quantity);
        batchAlerts.appendChild(row);
    }
}

async function loadDashboard() {
    statusMessage.textContent = "Loading inventory…";
    statusMessage.hidden = false;
    errorMessage.hidden = true;
    dashboardContent.hidden = true;
    refreshButton.disabled = true;

    try {
        const currentUser = await getCurrentUser();
        const destination = getDashboardForRole(currentUser.role);
        if (destination !== "inventory_dashboard.html") {
            window.location.replace(destination);
            return;
        }

        const [medicines, stockBatches, expiringResponse] = await Promise.all([
            loadAllActiveMedicines(),
            apiRequest("/api/v1/stock-batches"),
            apiRequest("/api/v1/stock-batches/expiring?days=30")
        ]);

        const lowStockCount = medicines.filter((medicine) =>
            Number(medicine.stock ?? 0) <= Number(medicine.reorder_threshold ?? 10)
        ).length;
        const outOfStockCount = medicines.filter((medicine) =>
            Number(medicine.stock ?? 0) <= 0
        ).length;
        const totalUnits = stockBatches.reduce(
            (total, batch) => total + Math.max(Number(batch.quantity ?? 0), 0),
            0
        );
        const expiredCount = (expiringResponse.items || []).filter(
            (batch) => batch.alert_status === "expired"
        ).length;
        const expiringCount = (expiringResponse.items || []).filter(
            (batch) => batch.alert_status === "expiring_soon"
        ).length;

        setText("activeMedicineCount", numberFormatter.format(medicines.length));
        setText("lowStockCount", numberFormatter.format(lowStockCount));
        setText("outOfStockCount", numberFormatter.format(outOfStockCount));
        setText("totalUnits", numberFormatter.format(totalUnits));
        setText("expiredBatchCount", numberFormatter.format(expiredCount));
        setText("expiringBatchCount", numberFormatter.format(expiringCount));
        renderLowStock(medicines);
        renderBatchAlerts(expiringResponse);

        statusMessage.hidden = true;
        dashboardContent.hidden = false;
    } catch (error) {
        statusMessage.hidden = true;
        errorMessage.textContent = error.message || "Unable to load the inventory dashboard.";
        errorMessage.hidden = false;

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    } finally {
        refreshButton.disabled = false;
    }
}

refreshButton.addEventListener("click", loadDashboard);
loadDashboard();
