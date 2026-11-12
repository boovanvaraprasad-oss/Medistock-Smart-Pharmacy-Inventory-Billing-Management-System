const auditRows = document.getElementById("auditRows");
const auditPageSize = 25;
let auditPage = 1;
let auditTotal = 0;

const auditActionLabels = {
    BILL_COMPLETE: "Bill completed", BILL_RETURN: "Bill returned",
    STOCK_ADJUSTMENT: "Stock adjusted", STOCK_REDUCE: "Stock reduced", STOCK_BATCH_CREATE: "Stock batch created",
    PURCHASE_ORDER_CREATE: "Purchase order created", PURCHASE_ORDER_UPDATE: "Purchase order changed",
    PURCHASE_ORDER_ITEM_ADD: "Purchase item added", PURCHASE_ORDER_ITEM_UPDATE: "Purchase item changed",
    PURCHASE_ORDER_RECEIVE: "Purchase order received", USER_CREATE: "Staff account created",
    USER_UPDATE: "Staff account changed", USER_DELETE: "Staff account deleted",
    MASTER_DATA_DELETE: "Master data deleted"
};
const auditEntityLabels = {
    bills: "Bill", medicines: "Medicine", stock_batches: "Stock batch",
    purchase_orders: "Purchase order", users: "Staff account",
    categories: "Category", manufacturers: "Manufacturer", units: "Unit", suppliers: "Supplier"
};

function appendAuditCell(row, text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) cell.className = className;
    row.append(cell);
    return cell;
}

function auditTimestamp(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }).format(date);
}

function auditDetailsText(details) {
    return Object.entries(details || {}).map(([key, value]) => {
        const label = key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
        const shownValue = typeof value === "object" && value !== null ? JSON.stringify(value) : String(value);
        return `${label}: ${shownValue}`;
    }).join(" · ") || "—";
}

function renderAuditRows(items) {
    auditRows.replaceChildren();
    document.getElementById("auditEmpty").hidden = items.length > 0;
    for (const entry of items) {
        const row = document.createElement("tr");
        appendAuditCell(row, auditTimestamp(entry.created_at));
        appendAuditCell(row, auditActionLabels[entry.action] || entry.action, "audit-action");
        const entityType = auditEntityLabels[entry.entity_type] || entry.entity_type || "Record";
        const recordRef = entry.entity_label && entry.entity_label !== entry.entity_id
            ? entry.entity_label
            : entry.entity_id
                ? `#${entry.entity_id.slice(-6)}`
                : "—";
        const recordCell = appendAuditCell(row, `${entityType} · ${recordRef}`);
        if (entry.entity_id) recordCell.title = `Record ID: ${entry.entity_id}`;
        const actor = entry.actor_name || entry.actor_email || "Unknown user";
        const role = (entry.actor_role || "unknown").replaceAll("_", " ");
        appendAuditCell(row, `${actor} · ${role}`);
        appendAuditCell(row, auditDetailsText(entry.details), "audit-details");
        auditRows.append(row);
    }
}

async function loadAuditTrail() {
    const status = document.getElementById("auditStatus");
    const error = document.getElementById("auditError");
    status.hidden = false;
    status.textContent = "Loading audit events…";
    error.hidden = true;
    document.getElementById("auditRefresh").disabled = true;
    try {
        const user = await getCurrentUser();
        if (!["owner", "compliance_officer"].includes(user.role)) {
            window.location.replace(getDashboardForRole(user.role));
            return;
        }
        const params = new URLSearchParams({ page: String(auditPage), limit: String(auditPageSize) });
        const q = document.getElementById("auditSearch").value.trim();
        const action = document.getElementById("auditAction").value;
        const entity = document.getElementById("auditEntity").value;
        if (q) params.set("q", q);
        if (action) params.set("action", action);
        if (entity) params.set("entity_type", entity);
        const data = await apiRequest(`/api/v1/audit-logs?${params}`);
        auditTotal = data.total;
        renderAuditRows(data.items);
        document.getElementById("auditCount").textContent = new Intl.NumberFormat("en-IN").format(auditTotal);
        const pageCount = Math.max(1, Math.ceil(auditTotal / auditPageSize));
        document.getElementById("auditPageLabel").textContent = `Page ${auditPage} of ${pageCount}`;
        document.getElementById("auditPrevious").disabled = auditPage <= 1;
        document.getElementById("auditNext").disabled = auditPage >= pageCount;
        status.hidden = true;
    } catch (caught) {
        status.hidden = true;
        error.textContent = caught.message || "Unable to load the audit trail.";
        error.hidden = false;
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    } finally {
        document.getElementById("auditRefresh").disabled = false;
    }
}

document.getElementById("auditFilters").addEventListener("submit", (event) => { event.preventDefault(); auditPage = 1; loadAuditTrail(); });
document.getElementById("auditRefresh").addEventListener("click", loadAuditTrail);
document.getElementById("auditPrevious").addEventListener("click", () => { if (auditPage > 1) { auditPage -= 1; loadAuditTrail(); } });
document.getElementById("auditNext").addEventListener("click", () => { if (auditPage * auditPageSize < auditTotal) { auditPage += 1; loadAuditTrail(); } });
loadAuditTrail();
