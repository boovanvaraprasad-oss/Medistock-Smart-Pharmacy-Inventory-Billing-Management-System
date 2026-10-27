const managerStatus = document.getElementById("statusMessage");
const managerError = document.getElementById("errorMessage");
const managerContent = document.getElementById("dashboardContent");
const managerRefresh = document.getElementById("refreshButton");
const managerNumber = new Intl.NumberFormat("en-IN");
const managerCurrency = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
let managerSales = null;

function managerText(id, value) { document.getElementById(id).textContent = value; }

function drawManagerSales() {
    if (!managerSales) return;
    const range = document.querySelector(".manager-range button[aria-pressed='true']")?.dataset.range || "day";
    let rows, amount, caption, label;
    if (range === "month") {
        rows = managerSales.monthly_daily_totals || [];
        amount = managerSales.monthly_sales_total || 0;
        caption = `${managerSales.current_month} · daily sales through today`;
        label = (entry) => entry.day;
    } else if (range === "year") {
        rows = managerSales.yearly_totals || [];
        amount = managerSales.completed_sales_total_all_time || 0;
        caption = "All-time sales grouped by year";
        label = (entry) => entry.year;
    } else {
        rows = managerSales.daily_hourly_totals || [];
        amount = managerSales.daily_sales_total || 0;
        const date = new Date(`${managerSales.current_date}T00:00:00`);
        caption = `Today, ${date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })} · sales by hour`;
        label = (entry) => String(entry.hour).padStart(2, "0");
    }
    managerText("salesCaption", caption);
    managerText("salesChartTotal", managerCurrency.format(managerSales.completed_sales_total_all_time || 0));
    const chart = document.getElementById("salesChart");
    chart.replaceChildren();
    const max = Math.max(...rows.map((entry) => Number(entry.total_amount) || 0), 1);
    const hasData = rows.some((entry) => Number(entry.total_amount) > 0);
    chart.hidden = !hasData;
    document.getElementById("salesChartEmpty").hidden = hasData;
    if (!hasData) return;
    chart.style.setProperty("--manager-points", rows.length);
    for (const entry of rows) {
        const group = document.createElement("div");
        group.className = "manager-bar-group";
        const bar = document.createElement("span");
        bar.className = "manager-bar";
        const value = Number(entry.total_amount) || 0;
        bar.style.height = `${Math.max(value / max * 100, value ? 4 : 2)}%`;
        group.title = `${label(entry)}: ${managerCurrency.format(value)}`;
        const track = document.createElement("span");
        track.className = "manager-bar-track";
        track.append(bar);
        const tick = document.createElement("small");
        tick.textContent = label(entry);
        group.append(track, tick);
        chart.append(group);
    }
}

function renderBills(bills) {
    const body = document.getElementById("recentBillRows");
    const completed = bills.filter((bill) => bill.is_active !== false).slice(0, 6);
    body.replaceChildren();
    document.getElementById("billsEmpty").hidden = completed.length > 0;
    for (const bill of completed) {
        const row = document.createElement("tr");
        for (const value of [bill.invoice_number || "—", bill.customer_name || "Walk-in customer"]) {
            const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
        }
        const statusCell = document.createElement("td");
        const badge = document.createElement("span"); badge.className = "manager-bill-status"; badge.dataset.status = bill.status || "draft"; badge.textContent = (bill.status || "draft").replaceAll("_", " "); statusCell.append(badge); row.append(statusCell);
        const total = document.createElement("td"); total.className = "manager-bill-total"; total.textContent = managerCurrency.format(Number(bill.total_amount) || 0); row.append(total);
        body.append(row);
    }
}

async function loadStoreManagerDashboard() {
    managerStatus.hidden = false; managerStatus.textContent = "Loading store overview…";
    managerError.hidden = true; managerContent.hidden = true; managerRefresh.disabled = true;
    try {
        const user = await getCurrentUser();
        if (getDashboardForRole(user.role) !== "store_manager_dashboard.html") { window.location.replace(getDashboardForRole(user.role)); return; }
        const [summary, bills, orders, suppliers] = await Promise.all([
            apiRequest("/api/v1/dashboard/summary"), apiRequest("/api/v1/bills"),
            apiRequest("/api/v1/purchase-orders"), apiRequest("/api/v1/suppliers")
        ]);
        const medicines = summary.medicines || {}, inventory = summary.inventory || {}, sales = summary.sales || {};
        const activeOrders = orders.filter((order) => order.is_active !== false);
        const draftCount = activeOrders.filter((order) => order.status === "draft").length;
        const orderedCount = activeOrders.filter((order) => order.status === "ordered").length;
        const openCount = draftCount + orderedCount;
        const supplierCount = suppliers.filter((supplier) => supplier.is_active !== false).length;
        managerText("activeMedicines", managerNumber.format(medicines.active_count || 0));
        managerText("lowStock", managerNumber.format(medicines.low_stock_count || 0));
        managerText("outOfStock", managerNumber.format(medicines.out_of_stock_count || 0));
        managerText("stockUnits", managerNumber.format(inventory.total_units || 0));
        managerText("salesAllTime", managerCurrency.format(sales.completed_sales_total_all_time || 0));
        managerText("openOrders", managerNumber.format(openCount));
        managerText("alertOut", managerNumber.format(medicines.out_of_stock_count || 0));
        managerText("alertExpiring", managerNumber.format(inventory.expiring_within_30_days_count || 0));
        managerText("alertOrders", managerNumber.format(openCount));
        managerText("alertExpired", managerNumber.format(inventory.expired_batch_count || 0));
        managerText("draftOrders", managerNumber.format(draftCount));
        managerText("orderedOrders", managerNumber.format(orderedCount));
        managerText("activeSuppliers", managerNumber.format(supplierCount));
        managerSales = sales;
        drawManagerSales();
        renderBills(bills);
        managerStatus.hidden = true; managerContent.hidden = false;
    } catch (error) {
        managerStatus.hidden = true;
        managerError.textContent = error.message || "Unable to load the Store Manager dashboard.";
        managerError.hidden = false;
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    } finally { managerRefresh.disabled = false; }
}

document.querySelectorAll(".manager-range button").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll(".manager-range button").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    drawManagerSales();
}));
managerRefresh.addEventListener("click", loadStoreManagerDashboard);
loadStoreManagerDashboard();
