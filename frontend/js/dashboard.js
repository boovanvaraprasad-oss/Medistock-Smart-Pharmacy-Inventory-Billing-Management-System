const loadingMessage = document.getElementById("loadingMessage");
const errorMessage = document.getElementById("errorMessage");
const dashboardContent = document.getElementById("dashboardContent");
const refreshButton = document.getElementById("refreshButton");
let salesSummary = null;

const numberFormatter = new Intl.NumberFormat("en-IN");

const currencyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
});

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function updateInventoryChart(activeCount, lowStockCount, outOfStockCount) {
    const total = Math.max(activeCount, 0);
    const outCount = Math.min(Math.max(outOfStockCount, 0), total);
    const lowCount = Math.min(
        Math.max(lowStockCount - outCount, 0),
        total - outCount
    );
    const healthyCount = Math.max(total - outCount - lowCount, 0);

    const healthyPercent = total ? (healthyCount / total) * 100 : 0;
    const lowPercent = total ? (lowCount / total) * 100 : 0;
    const outPercent = total ? (outCount / total) * 100 : 0;

    const lowEnd = healthyPercent + lowPercent;
    const outEnd = lowEnd + outPercent;

    const donut = document.getElementById("stockDonut");
    donut.style.background = total
        ? `conic-gradient(
            #159567 0% ${healthyPercent}%,
            #f0bb38 ${healthyPercent}% ${lowEnd}%,
            #e64b46 ${lowEnd}% ${outEnd}%,
            #e9efec ${outEnd}% 100%
        )`
        : "#e9efec";

    setText("donutTotal", numberFormatter.format(total));
    setText("healthyStockCount", numberFormatter.format(healthyCount));
    setText("legendLowStock", numberFormatter.format(lowCount));
    setText("legendOutOfStock", numberFormatter.format(outCount));
}

function renderSalesChart(chartId, emptyId, series, totalAmount, labelForEntry) {
    const chart = document.getElementById(chartId);
    const emptyMessage = document.getElementById(emptyId);
    chart.replaceChildren();

    if (!series.length || totalAmount <= 0) {
        chart.hidden = true;
        emptyMessage.hidden = false;
        return;
    }

    chart.hidden = false;
    emptyMessage.hidden = true;
    const maximum = Math.max(...series.map((entry) => entry.total_amount), 1);
    chart.style.setProperty("--sales-point-count", series.length);

    for (const entry of series) {
        const group = document.createElement("div");
        group.className = "sales-bar-group";
        const label = labelForEntry(entry);
        group.title = `${label}: ${currencyFormatter.format(entry.total_amount)}`;

        const amount = document.createElement("span");
        amount.className = "sales-bar-value";
        amount.textContent = currencyFormatter.format(entry.total_amount);

        const barTrack = document.createElement("div");
        barTrack.className = "sales-bar-track";

        const bar = document.createElement("div");
        bar.className = "sales-bar";
        const height = Math.max((entry.total_amount / maximum) * 100, 2);
        bar.style.height = `${height}%`;
        barTrack.append(bar);

        const year = document.createElement("span");
        year.className = "sales-bar-year";
        year.textContent = label;

        group.append(amount, barTrack, year);
        chart.append(group);
    }
}

function renderSelectedSalesRange() {
    if (!salesSummary) return;

    const selectedRange = document.querySelector('input[name="sales-range"]:checked')?.value || "day";
    document.querySelector(".cir-tabs")?.setAttribute("data-active-range", selectedRange);
    let series;
    let totalAmount;
    let caption;
    let labelForEntry;
    let chartLabel;

    if (selectedRange === "month") {
        series = salesSummary.monthly_daily_totals || [];
        totalAmount = salesSummary.monthly_sales_total || 0;
        caption = `${salesSummary.current_month} · daily sales through today`;
        labelForEntry = (entry) => entry.day;
        chartLabel = `Sales by day for ${salesSummary.current_month}`;
    } else if (selectedRange === "year") {
        series = salesSummary.yearly_totals || [];
        totalAmount = salesSummary.completed_sales_total_all_time || 0;
        caption = "All-time sales grouped by year";
        labelForEntry = (entry) => entry.year;
        chartLabel = "All-time sales by year";
    } else {
        series = salesSummary.daily_hourly_totals || [];
        totalAmount = salesSummary.daily_sales_total || 0;
        const today = new Date(`${salesSummary.current_date}T00:00:00`);
        caption = `Today, ${today.toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric"
        })} · sales by hour`;
        labelForEntry = (entry) => String(entry.hour).padStart(2, "0");
        chartLabel = "Today's sales by hour";
    }

    setText("salesRangeCaption", caption);
    setText("salesGraphTotal", currencyFormatter.format(salesSummary.completed_sales_total_all_time || 0));
    const chart = document.getElementById("salesChart");
    chart.setAttribute("aria-label", chartLabel);
    renderSalesChart("salesChart", "salesChartEmpty", series, totalAmount, labelForEntry);
}

function setTodayDate() {
    setText(
        "todayDate",
        new Date().toLocaleDateString("en-IN", {
            weekday: "short",
            day: "numeric",
            month: "short",
            year: "numeric"
        })
    );
}

async function loadDashboard() {
    loadingMessage.hidden = false;
    errorMessage.hidden = true;
    dashboardContent.hidden = true;
    refreshButton.disabled = true;

    try {
        const currentUser = await getCurrentUser();
        const permissions = currentUser.permissions || [];

        // Roles with a dedicated dashboard should not load this owner overview,
        // even when they open its URL directly.
        const roleDashboard = getDashboardForRole(currentUser.role);
        if (roleDashboard !== "dashboard.html") {
            window.location.replace(roleDashboard);
            return;
        }

        const roleLabel = (currentUser.role || "staff")
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());

        // Avoid showing a raw API 403 for roles whose dashboards have not
        // been built yet. The summary endpoint is intentionally report-only.
        if (!permissions.includes("report:view")) {
            loadingMessage.hidden = true;
            errorMessage.textContent = `The ${roleLabel} dashboard is not available yet. Please contact the owner.`;
            errorMessage.hidden = false;
            return;
        }

        const summary = await apiRequest("/api/v1/dashboard/summary");

        const activeCount = summary.medicines.active_count;
        const lowStockCount = summary.medicines.low_stock_count;
        const outOfStockCount = summary.medicines.out_of_stock_count;
        const expiredCount = summary.inventory.expired_batch_count;
        const expiringCount =
            summary.inventory.expiring_within_30_days_count;
        const openOrdersCount =
            summary.purchasing.open_purchase_order_count;

        setText("activeMedicineCount", numberFormatter.format(activeCount));
        setText("lowStockCount", numberFormatter.format(lowStockCount));
        setText("outOfStockCount", numberFormatter.format(outOfStockCount));
        setText(
            "totalStockUnits",
            numberFormatter.format(summary.inventory.total_units)
        );
        setText(
            "inventoryValue",
            currencyFormatter.format(summary.inventory.purchase_cost_value)
        );
        setText("expiredBatchCount", numberFormatter.format(expiredCount));
        setText("expiringBatchCount", numberFormatter.format(expiringCount));
        setText("openPurchaseOrderCount", numberFormatter.format(openOrdersCount));

        setText("alertExpiredCount", numberFormatter.format(expiredCount));
        setText("alertExpiringCount", numberFormatter.format(expiringCount));
        setText("alertOrdersCount", numberFormatter.format(openOrdersCount));

        updateInventoryChart(activeCount, lowStockCount, outOfStockCount);
        salesSummary = summary.sales;
        renderSelectedSalesRange();

        const updatedAt = new Date(summary.generated_at);
        setText(
            "updatedAt",
            `Updated ${updatedAt.toLocaleTimeString("en-IN", {
                hour: "numeric",
                minute: "2-digit"
            })}`
        );

        dashboardContent.hidden = false;
        loadingMessage.hidden = true;
    } catch (error) {
        loadingMessage.hidden = true;
        errorMessage.textContent = error.message;
        errorMessage.hidden = false;

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    } finally {
        refreshButton.disabled = false;
    }
}

setTodayDate();
refreshButton.addEventListener("click", loadDashboard);
document.querySelectorAll('input[name="sales-range"]').forEach((input) => {
    input.addEventListener("change", renderSelectedSalesRange);
});

if (!localStorage.getItem("access_token")) {
    window.location.href = "/";
} else {
    loadDashboard();
}
