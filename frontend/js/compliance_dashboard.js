const complianceStatus = document.getElementById("statusMessage");
const complianceError = document.getElementById("errorMessage");
const complianceContent = document.getElementById("dashboardContent");
const complianceRefresh = document.getElementById("refreshButton");
const complianceNumber = new Intl.NumberFormat("en-IN");
const complianceCurrency = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });

function complianceSet(id, value) { document.getElementById(id).textContent = value; }

function complianceCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.append(cell);
    return cell;
}

function renderStaff(users) {
    const body = document.getElementById("staffRows");
    body.replaceChildren();
    const active = users.filter((user) => user.is_active !== false);
    document.getElementById("staffEmpty").hidden = users.length > 0;
    complianceSet("staffCount", complianceNumber.format(users.length));
    complianceSet("activeStaffCount", `${complianceNumber.format(active.length)} active`);
    users.slice(0, 8).forEach((user) => {
        const row = document.createElement("tr");
        complianceCell(row, user.email || "Unknown account");
        complianceCell(row, (user.role || "unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()));
        const state = complianceCell(row, user.is_active === false ? "Inactive" : "Active");
        state.className = user.is_active === false ? "compliance-state state-inactive" : "compliance-state state-active";
        body.append(row);
    });
}

function renderControlledMedicines(medicines) {
    const container = document.getElementById("controlledMedicines");
    const controlled = medicines.filter((medicine) => medicine.is_active !== false && medicine.is_controlled_substance);
    container.replaceChildren();
    document.getElementById("controlledEmpty").hidden = controlled.length > 0;
    complianceSet("controlledCount", complianceNumber.format(controlled.length));
    controlled.slice(0, 8).forEach((medicine) => {
        const item = document.createElement("article");
        item.className = "controlled-entry";
        const name = document.createElement("strong"); name.textContent = medicine.name || "Unnamed medicine";
        const detail = document.createElement("small"); detail.textContent = `${medicine.sku || "No SKU"} · Stock ${complianceNumber.format(medicine.stock || 0)}`;
        item.append(name, detail);
        container.append(item);
    });
}

function renderBatches(result) {
    const batches = result.items || [];
    const body = document.getElementById("batchRows");
    body.replaceChildren();
    document.getElementById("batchEmpty").hidden = batches.length > 0;
    complianceSet("expiringCount", complianceNumber.format(batches.filter((batch) => batch.alert_status === "expiring_soon").length));
    complianceSet("expiredCount", complianceNumber.format(batches.filter((batch) => batch.alert_status === "expired").length));
    batches.slice(0, 8).forEach((batch) => {
        const row = document.createElement("tr");
        complianceCell(row, batch.medicine_name || "Unknown medicine");
        complianceCell(row, batch.batch_number || "—");
        complianceCell(row, complianceNumber.format(batch.quantity || 0));
        complianceCell(row, batch.expiry_date ? new Date(`${batch.expiry_date}T00:00:00`).toLocaleDateString("en-IN") : "—");
        const status = complianceCell(row, batch.alert_status === "expired" ? "Expired" : "Expiring");
        status.className = batch.alert_status === "expired" ? "compliance-state state-inactive" : "compliance-state state-warning";
        body.append(row);
    });
}

function renderBills(bills) {
    const relevant = bills.filter((bill) => bill.is_active !== false).slice(0, 8);
    const body = document.getElementById("billRows");
    body.replaceChildren();
    document.getElementById("billsEmpty").hidden = relevant.length > 0;
    relevant.forEach((bill) => {
        const row = document.createElement("tr");
        complianceCell(row, bill.invoice_number || "—");
        complianceCell(row, bill.customer_name || "Walk-in customer");
        const state = complianceCell(row, (bill.status || "unknown").replaceAll("_", " "));
        state.className = bill.status === "completed" ? "compliance-state state-active" : "compliance-state";
        complianceCell(row, complianceCurrency.format(Number(bill.total_amount) || 0));
        body.append(row);
    });
}

async function loadAllMedicines() {
    const firstPage = await apiRequest("/api/v1/medicines?page=1&limit=100");
    const pages = Math.ceil((firstPage.total || firstPage.items.length) / firstPage.limit);
    if (pages <= 1) return firstPage.items || [];
    const remainingPages = await Promise.all(Array.from({ length: pages - 1 }, (_, index) =>
        apiRequest(`/api/v1/medicines?page=${index + 2}&limit=100`)
    ));
    return [...(firstPage.items || []), ...remainingPages.flatMap((page) => page.items || [])];
}

async function loadComplianceDashboard() {
    complianceStatus.hidden = false;
    complianceStatus.textContent = "Loading compliance overview…";
    complianceError.hidden = true;
    complianceContent.hidden = true;
    complianceRefresh.disabled = true;
    try {
        const user = await getCurrentUser();
        if (getDashboardForRole(user.role) !== "compliance_dashboard.html") {
            window.location.replace(getDashboardForRole(user.role));
            return;
        }
        const [summary, users, medicines, batches, bills] = await Promise.all([
            apiRequest("/api/v1/dashboard/summary"),
            apiRequest("/api/v1/users"),
            loadAllMedicines(),
            apiRequest("/api/v1/stock-batches/expiring?days=30"),
            apiRequest("/api/v1/bills")
        ]);
        renderStaff(users);
        renderControlledMedicines(medicines);
        renderBatches(batches);
        renderBills(bills);
        const sales = summary.sales || {};
        complianceSet("completedBillCount", complianceNumber.format(sales.completed_bill_count_all_time || 0));
        complianceSet("salesTotal", complianceCurrency.format(sales.completed_sales_total_all_time || 0));
        complianceStatus.hidden = true;
        complianceContent.hidden = false;
    } catch (error) {
        complianceStatus.hidden = true;
        complianceError.textContent = error.message || "Unable to load the Compliance dashboard.";
        complianceError.hidden = false;
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    } finally {
        complianceRefresh.disabled = false;
    }
}

complianceRefresh.addEventListener("click", loadComplianceDashboard);
loadComplianceDashboard();
