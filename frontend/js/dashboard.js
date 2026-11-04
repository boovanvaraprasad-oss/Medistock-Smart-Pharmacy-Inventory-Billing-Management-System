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

function renderCategoryDistribution(categories = []) {
    const container = document.getElementById("stockCategoryBreakdown");
    container.replaceChildren();

    if (!categories.length) {
        const empty = document.createElement("p");
        empty.className = "chart-empty";
        empty.textContent = "No stocked categories to show yet.";
        container.append(empty);
        return;
    }

    categories.forEach((category) => {
        const row = document.createElement("div");
        row.className = "category-distribution-row";

        const labels = document.createElement("div");
        labels.className = "category-distribution-labels";

        const name = document.createElement("span");
        name.textContent = category.category_name || "Uncategorized";

        const value = document.createElement("strong");
        value.textContent = `${category.percentage || 0}% (${currencyFormatter.format(category.stock_value || 0)})`;
        labels.append(name, value);

        const track = document.createElement("div");
        track.className = "category-distribution-track";

        const bar = document.createElement("span");
        bar.className = "category-distribution-fill";
        bar.style.width = `${Math.max(0, Math.min(Number(category.percentage) || 0, 100))}%`;
        track.append(bar);

        row.append(labels, track);
        container.append(row);
    });
}

function renderTopSellingMedicines(records = []) {
    const list = document.getElementById("topMedicines");
    const emptyMessage = document.getElementById("topMedicinesEmpty");
    list.replaceChildren();
    emptyMessage.hidden = records.length > 0;

    records.forEach((medicine, index) => {
        const row = document.createElement("div");
        row.className = "top-medicine-row";

        const rank = document.createElement("span");
        rank.className = "top-medicine-rank";
        rank.textContent = String(index + 1).padStart(2, "0");

        const copy = document.createElement("span");
        copy.className = "top-medicine-copy";

        const name = document.createElement("strong");
        name.textContent = medicine.medicine_name || "Unknown medicine";

        const units = document.createElement("small");
        units.textContent = `${numberFormatter.format(medicine.units_sold || 0)} units sold`;
        copy.append(name, units);

        const revenue = document.createElement("strong");
        revenue.className = "top-medicine-revenue";
        revenue.textContent = currencyFormatter.format(medicine.revenue || 0);

        row.append(rank, copy, revenue);
        list.append(row);
    });
}

function renderLowStockAlerts(records = []) {
    const list = document.getElementById("ownerLowStockAlerts");
    list.replaceChildren();
    if (!records.length) return;

    const heading = document.createElement("h3");
    heading.className = "low-stock-list-title";
    heading.textContent = "Medicines to restock";
    list.append(heading);

    records.slice(0, 5).forEach((medicine) => {
        const link = document.createElement("a");
        link.className = `low-stock-alert-row${medicine.stock <= 0 ? " is-empty" : ""}`;
        link.href = `medicines.html?search=${encodeURIComponent(medicine.name || "")}`;
        const copy = document.createElement("span");
        const name = document.createElement("strong");
        name.textContent = medicine.name || "Medicine";
        const sku = document.createElement("small");
        sku.textContent = medicine.sku ? `SKU: ${medicine.sku}` : `Minimum level: ${medicine.threshold}`;
        copy.append(name, sku);
        const stock = document.createElement("strong");
        stock.className = "low-stock-alert-value";
        stock.textContent = medicine.stock <= 0 ? "Out of stock" : `${numberFormatter.format(medicine.stock)} left`;
        link.append(copy, stock);
        list.append(link);
    });
}

function renderSalesChart(chartId, emptyId, series, labelForEntry) {
    const chart = document.getElementById(chartId);
    const emptyMessage = document.getElementById(emptyId);
    chart.replaceChildren();

    if (!series.length || !series.some((entry) => entry.total_amount > 0 || entry.purchase_amount > 0)) {
        chart.hidden = true;
        emptyMessage.hidden = false;
        return;
    }

    chart.hidden = false;
    emptyMessage.hidden = true;
    const svgNamespace = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNamespace, "svg");
    const width = 960;
    const height = 280;
    const left = 64;
    const right = 14;
    const top = 14;
    const bottom = 38;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;
    const maximum = Math.max(...series.flatMap((entry) => [entry.total_amount || 0, entry.purchase_amount || 0]), 1);
    const step = Math.max(1, Math.ceil(maximum / 4 / 100) * 100);
    const axisMaximum = Math.max(step * 4, step);
    const makePoints = (valueKey) => series.map((entry, index) => ({
        x: left + (series.length === 1 ? plotWidth / 2 : (index / (series.length - 1)) * plotWidth),
        y: top + plotHeight - (Math.max(entry[valueKey] || 0, 0) / axisMaximum) * plotHeight,
        amount: entry[valueKey] || 0,
        label: labelForEntry(entry)
    }));
    const salesPoints = makePoints("total_amount");
    const purchasePoints = makePoints("purchase_amount");

    svg.setAttribute("class", "sales-area-svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");

    const defs = document.createElementNS(svgNamespace, "defs");
    const gradient = document.createElementNS(svgNamespace, "linearGradient");
    gradient.id = "salesAreaGradient";
    gradient.setAttribute("x1", "0");
    gradient.setAttribute("x2", "0");
    gradient.setAttribute("y1", "0");
    gradient.setAttribute("y2", "1");
    const stopTop = document.createElementNS(svgNamespace, "stop");
    stopTop.setAttribute("offset", "0%");
    stopTop.setAttribute("stop-color", "#10a879");
    stopTop.setAttribute("stop-opacity", "0.28");
    const stopBottom = document.createElementNS(svgNamespace, "stop");
    stopBottom.setAttribute("offset", "100%");
    stopBottom.setAttribute("stop-color", "#10a879");
    stopBottom.setAttribute("stop-opacity", "0.015");
    gradient.append(stopTop, stopBottom);
    defs.append(gradient);
    svg.append(defs);

    for (let tick = 0; tick <= 4; tick += 1) {
        const y = top + (plotHeight / 4) * tick;
        const gridLine = document.createElementNS(svgNamespace, "line");
        gridLine.setAttribute("x1", String(left));
        gridLine.setAttribute("x2", String(width - right));
        gridLine.setAttribute("y1", String(y));
        gridLine.setAttribute("y2", String(y));
        gridLine.setAttribute("class", "sales-grid-line");
        svg.append(gridLine);

        const axisLabel = document.createElementNS(svgNamespace, "text");
        axisLabel.setAttribute("x", String(left - 10));
        axisLabel.setAttribute("y", String(y + 4));
        axisLabel.setAttribute("text-anchor", "end");
        axisLabel.setAttribute("class", "sales-axis-label");
        axisLabel.textContent = numberFormatter.format(axisMaximum - step * tick);
        svg.append(axisLabel);
    }

    const buildLinePath = (points) => {
        let path = `M ${points[0].x} ${points[0].y}`;
        for (let index = 0; index < points.length - 1; index += 1) {
            const current = points[index];
            const next = points[index + 1];
            const midpointX = (current.x + next.x) / 2;
            const midpointY = (current.y + next.y) / 2;
            path += ` Q ${current.x} ${current.y} ${midpointX} ${midpointY}`;
        }
        const last = points[points.length - 1];
        return `${path} T ${last.x} ${last.y}`;
    };
    const linePath = buildLinePath(salesPoints);
    const purchasePath = buildLinePath(purchasePoints);
    const lastPoint = salesPoints[salesPoints.length - 1];

    const areaPath = `${linePath} L ${lastPoint.x} ${top + plotHeight} L ${salesPoints[0].x} ${top + plotHeight} Z`;
    const area = document.createElementNS(svgNamespace, "path");
    area.setAttribute("d", areaPath);
    area.setAttribute("fill", "url(#salesAreaGradient)");
    svg.append(area);

    const line = document.createElementNS(svgNamespace, "path");
    line.setAttribute("d", linePath);
    line.setAttribute("fill", "none");
    line.setAttribute("stroke", "#0c9b70");
    line.setAttribute("stroke-width", "3");
    line.setAttribute("stroke-linecap", "round");
    line.setAttribute("stroke-linejoin", "round");
    svg.append(line);

    const purchaseLine = document.createElementNS(svgNamespace, "path");
    purchaseLine.setAttribute("d", purchasePath);
    purchaseLine.setAttribute("fill", "none");
    purchaseLine.setAttribute("stroke", "#94a3b8");
    purchaseLine.setAttribute("stroke-width", "2.5");
    purchaseLine.setAttribute("stroke-dasharray", "6 5");
    purchaseLine.setAttribute("stroke-linecap", "round");
    purchaseLine.setAttribute("stroke-linejoin", "round");
    svg.append(purchaseLine);

    const labelStride = Math.max(1, Math.ceil(salesPoints.length / 8));
    salesPoints.forEach((point, index) => {
        const salesCircle = document.createElementNS(svgNamespace, "circle");
        salesCircle.setAttribute("cx", String(point.x));
        salesCircle.setAttribute("cy", String(point.y));
        salesCircle.setAttribute("r", salesPoints.length > 16 ? "2.5" : "4");
        salesCircle.setAttribute("class", "sales-chart-point");
        const salesTitle = document.createElementNS(svgNamespace, "title");
        salesTitle.textContent = `Revenue · ${point.label}: ${currencyFormatter.format(point.amount)}`;
        salesCircle.append(salesTitle);
        svg.append(salesCircle);

        if (index % labelStride === 0 || index === salesPoints.length - 1) {
            const xLabel = document.createElementNS(svgNamespace, "text");
            xLabel.setAttribute("x", String(point.x));
            xLabel.setAttribute("y", String(height - 8));
            xLabel.setAttribute("text-anchor", "middle");
            xLabel.setAttribute("class", "sales-axis-label sales-x-label");
            xLabel.textContent = point.label;
            svg.append(xLabel);
        }

        const purchaseCircle = document.createElementNS(svgNamespace, "circle");
        purchaseCircle.setAttribute("cx", String(purchasePoints[index].x));
        purchaseCircle.setAttribute("cy", String(purchasePoints[index].y));
        purchaseCircle.setAttribute("r", salesPoints.length > 16 ? "2" : "3");
        purchaseCircle.setAttribute("class", "purchase-chart-point");
        const purchaseTitle = document.createElementNS(svgNamespace, "title");
        purchaseTitle.textContent = `Purchases · ${point.label}: ${currencyFormatter.format(purchasePoints[index].amount)}`;
        purchaseCircle.append(purchaseTitle);
        svg.append(purchaseCircle);
    });

    chart.append(svg);
}

function renderSelectedSalesRange() {
    if (!salesSummary) return;

    const selectedRange = document.querySelector('input[name="sales-range"]:checked')?.value || "day";
    document.querySelector(".cir-tabs")?.setAttribute("data-active-range", selectedRange);
    let series;
    let caption;
    let labelForEntry;
    let chartLabel;

    if (selectedRange === "month") {
        series = salesSummary.monthly_daily_totals || [];
        caption = `${salesSummary.current_month} · daily sales through today`;
        labelForEntry = (entry) => entry.day;
        chartLabel = `Sales by day for ${salesSummary.current_month}`;
    } else if (selectedRange === "year") {
        series = salesSummary.yearly_totals || [];
        caption = "All-time sales grouped by year";
        labelForEntry = (entry) => entry.year;
        chartLabel = "All-time sales by year";
    } else {
        series = salesSummary.daily_hourly_totals || [];
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
    renderSalesChart("salesChart", "salesChartEmpty", series, labelForEntry);
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
        setText("activeMedicineSummary", `${numberFormatter.format(activeCount)} active medicine SKUs`);
        setText("lowStockCount", numberFormatter.format(lowStockCount));
        setText("outOfStockCount", numberFormatter.format(outOfStockCount));
        setText("dailySalesRevenue", currencyFormatter.format(summary.sales.daily_sales_total || 0));
        setText(
            "completedBillCountToday",
            `${numberFormatter.format(summary.sales.daily_completed_bill_count || 0)} completed bills today`
        );
        const comparison = document.getElementById("dailySalesComparison");
        const change = summary.sales.daily_sales_change_percentage;
        comparison.classList.remove("is-positive", "is-negative");
        if (change === null || change === undefined) {
            comparison.textContent = "No sales yesterday to compare";
        } else {
            const sign = change > 0 ? "+" : "";
            comparison.textContent = `${sign}${change}% vs yesterday`;
            comparison.classList.add(change >= 0 ? "is-positive" : "is-negative");
        }
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

        renderCategoryDistribution(summary.category_distribution || []);
        renderTopSellingMedicines(summary.top_selling_medicines || []);
        renderLowStockAlerts(summary.alerts?.low_stock_medicines || []);
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
