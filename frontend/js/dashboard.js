const loadingMessage = document.getElementById("loadingMessage");
const errorMessage = document.getElementById("errorMessage");
const dashboardContent = document.getElementById("dashboardContent");
const refreshButton = document.getElementById("refreshButton");
let salesSummary = null;
let salesChartRequest = 0;

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

function renderSalesChart(chartId, emptyId, series, labelForEntry, tooltipLabelForEntry = labelForEntry) {
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
        label: labelForEntry(entry),
        tooltipLabel: tooltipLabelForEntry(entry)
    }));
    const salesPoints = makePoints("total_amount");
    const purchasePoints = makePoints("purchase_amount");
    const isDark = document.documentElement.dataset.theme === "dark";
    const revenueColor = isDark ? "#22b9b5" : "#0b9c9d";
    const purchaseColor = isDark ? "#b8cedd" : "#8ba6bd";

    svg.setAttribute("class", "sales-area-svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("role", "group");
    svg.setAttribute("aria-label", "Revenue and received purchases by selected time interval");

    const defs = document.createElementNS(svgNamespace, "defs");
    const gradient = document.createElementNS(svgNamespace, "linearGradient");
    gradient.id = "salesAreaGradient";
    gradient.setAttribute("x1", "0");
    gradient.setAttribute("x2", "0");
    gradient.setAttribute("y1", "0");
    gradient.setAttribute("y2", "1");
    const stopTop = document.createElementNS(svgNamespace, "stop");
    stopTop.setAttribute("offset", "0%");
    stopTop.setAttribute("stop-color", revenueColor);
    stopTop.setAttribute("stop-opacity", "0.28");
    const stopBottom = document.createElementNS(svgNamespace, "stop");
    stopBottom.setAttribute("offset", "100%");
    stopBottom.setAttribute("stop-color", revenueColor);
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
    area.setAttribute("class", "sales-area-fill");
    svg.append(area);

    const line = document.createElementNS(svgNamespace, "path");
    line.setAttribute("d", linePath);
    line.setAttribute("fill", "none");
    line.setAttribute("stroke", revenueColor);
    line.setAttribute("stroke-width", "3");
    line.setAttribute("stroke-linecap", "round");
    line.setAttribute("stroke-linejoin", "round");
    line.setAttribute("class", "sales-revenue-line");
    svg.append(line);

    const purchaseLine = document.createElementNS(svgNamespace, "path");
    purchaseLine.setAttribute("d", purchasePath);
    purchaseLine.setAttribute("fill", "none");
    purchaseLine.setAttribute("stroke", purchaseColor);
    purchaseLine.setAttribute("stroke-width", "2.5");
    purchaseLine.setAttribute("stroke-linecap", "round");
    purchaseLine.setAttribute("stroke-linejoin", "round");
    purchaseLine.setAttribute("class", "sales-purchases-line");
    svg.append(purchaseLine);
    chart.append(svg);

    [line, purchaseLine].forEach((chartLine) => {
        try {
            const pathLength = chartLine.getTotalLength();
            chartLine.style.setProperty("--sales-line-length", `${pathLength}px`);
            chartLine.style.strokeDasharray = `${pathLength}`;
            chartLine.style.strokeDashoffset = `${pathLength}`;
        } catch {
            // Keep the chart visible if an SVG implementation cannot measure paths.
        }
    });

    const labelStride = Math.max(1, Math.ceil(salesPoints.length / 8));
    salesPoints.forEach((point, index) => {
        const salesCircle = document.createElementNS(svgNamespace, "circle");
        salesCircle.setAttribute("cx", String(point.x));
        salesCircle.setAttribute("cy", String(point.y));
        salesCircle.setAttribute("r", salesPoints.length > 16 ? "2.5" : "4");
        salesCircle.setAttribute("class", "sales-chart-point");
        salesCircle.setAttribute("tabindex", "0");
        salesCircle.setAttribute("aria-label", `Revenue · ${point.label}: ${currencyFormatter.format(point.amount)}`);
        salesCircle.dataset.pointIndex = String(index);
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
        purchaseCircle.setAttribute("tabindex", "0");
        purchaseCircle.setAttribute("aria-label", `Purchases · ${point.label}: ${currencyFormatter.format(purchasePoints[index].amount)}`);
        purchaseCircle.dataset.pointIndex = String(index);
        svg.append(purchaseCircle);
    });

    const hoverLine = document.createElementNS(svgNamespace, "line");
    hoverLine.setAttribute("class", "sales-chart-crosshair");
    hoverLine.setAttribute("y1", String(top));
    hoverLine.setAttribute("y2", String(top + plotHeight));
    hoverLine.style.display = "none";
    svg.append(hoverLine);

    const revenueHoverDot = document.createElementNS(svgNamespace, "circle");
    revenueHoverDot.setAttribute("class", "sales-chart-active-dot revenue");
    revenueHoverDot.setAttribute("r", "5");
    revenueHoverDot.style.display = "none";
    const purchasesHoverDot = document.createElementNS(svgNamespace, "circle");
    purchasesHoverDot.setAttribute("class", "sales-chart-active-dot purchases");
    purchasesHoverDot.setAttribute("r", "5");
    purchasesHoverDot.style.display = "none";
    svg.append(revenueHoverDot, purchasesHoverDot);

    const tooltip = document.createElement("div");
    tooltip.className = "sales-chart-tooltip";
    tooltip.id = `${chartId}Tooltip`;
    tooltip.setAttribute("role", "tooltip");
    tooltip.hidden = true;
    chart.append(svg, tooltip);

    const showTooltip = (index, clientX, clientY) => {
        const revenuePoint = salesPoints[index];
        const purchasesPoint = purchasePoints[index];
        if (!revenuePoint || !purchasesPoint) return;
        hoverLine.setAttribute("x1", String(revenuePoint.x));
        hoverLine.setAttribute("x2", String(revenuePoint.x));
        hoverLine.style.display = "";
        revenueHoverDot.setAttribute("cx", String(revenuePoint.x));
        revenueHoverDot.setAttribute("cy", String(revenuePoint.y));
        revenueHoverDot.style.display = "";
        purchasesHoverDot.setAttribute("cx", String(purchasesPoint.x));
        purchasesHoverDot.setAttribute("cy", String(purchasesPoint.y));
        purchasesHoverDot.style.display = "";
        tooltip.replaceChildren();

        const heading = document.createElement("strong");
        heading.className = "sales-tooltip-date";
        heading.textContent = revenuePoint.tooltipLabel;
        tooltip.append(heading);

        [
            { label: "Revenue", amount: revenuePoint.amount, className: "revenue" },
            { label: "Purchases", amount: purchasesPoint.amount, className: "purchases" }
        ].forEach((item) => {
            const row = document.createElement("div");
            row.className = "sales-tooltip-row";
            const name = document.createElement("span");
            const swatch = document.createElement("i");
            swatch.className = `sales-tooltip-swatch ${item.className}`;
            name.append(swatch, document.createTextNode(item.label));
            const value = document.createElement("strong");
            value.textContent = currencyFormatter.format(item.amount);
            row.append(name, value);
            tooltip.append(row);
        });

        tooltip.hidden = false;
        const chartRect = chart.getBoundingClientRect();
        const desiredLeft = clientX - chartRect.left + 12;
        const desiredTop = clientY - chartRect.top + 12;
        const leftPosition = Math.max(8, Math.min(desiredLeft, chart.clientWidth - tooltip.offsetWidth - 8));
        const topPosition = Math.max(8, Math.min(desiredTop, chart.clientHeight - tooltip.offsetHeight - 8));
        tooltip.style.left = `${leftPosition}px`;
        tooltip.style.top = `${topPosition}px`;
    };
    const hideTooltip = () => {
        tooltip.hidden = true;
        hoverLine.style.display = "none";
        revenueHoverDot.style.display = "none";
        purchasesHoverDot.style.display = "none";
    };

    svg.addEventListener("pointermove", (event) => {
        const bounds = svg.getBoundingClientRect();
        const viewX = ((event.clientX - bounds.left) / bounds.width) * width;
        const nearestIndex = salesPoints.reduce((bestIndex, point, index) =>
            Math.abs(point.x - viewX) < Math.abs(salesPoints[bestIndex].x - viewX) ? index : bestIndex, 0);
        showTooltip(nearestIndex, event.clientX, event.clientY);
    });
    svg.addEventListener("pointerleave", hideTooltip);
    svg.querySelectorAll(".sales-chart-point, .purchase-chart-point").forEach((point) => {
        point.setAttribute("aria-describedby", tooltip.id);
        point.addEventListener("focus", () => {
            const pointIndex = Number(point.dataset.pointIndex);
            const bounds = svg.getBoundingClientRect();
            const activePoint = salesPoints[pointIndex];
            showTooltip(pointIndex,
                bounds.left + (activePoint.x / width) * bounds.width,
                bounds.top + (activePoint.y / height) * bounds.height);
        });
        point.addEventListener("blur", hideTooltip);
    });
}

function renderSelectedSalesRange() {
    if (!salesSummary) return;

    const selectedRange = document.querySelector('input[name="sales-range"]:checked')?.value || "day";
    document.querySelector(".cir-tabs")?.setAttribute("data-active-range", selectedRange);
    let series;
    let caption;
    let labelForEntry;
    let tooltipLabelForEntry;
    let chartLabel;

    if (selectedRange === "month") {
        series = salesSummary.selected_month_daily_totals || salesSummary.monthly_daily_totals || [];
        caption = `${salesSummary.selected_month || salesSummary.current_month} · daily sales`;
        labelForEntry = (entry) => entry.day;
        tooltipLabelForEntry = (entry) => {
            const monthValue = document.getElementById("salesMonthInput").value;
            const dayValue = String(entry.day).padStart(2, "0");
            return new Date(`${monthValue}-${dayValue}T00:00:00`).toLocaleDateString("en-IN", {
                day: "numeric", month: "short", year: "numeric"
            });
        };
        chartLabel = `Sales by day for ${salesSummary.current_month}`;
    } else if (selectedRange === "year") {
        series = salesSummary.yearly_totals || [];
        caption = "All-time sales grouped by year";
        labelForEntry = (entry) => entry.year;
        tooltipLabelForEntry = (entry) => String(entry.year);
        chartLabel = "All-time sales by year";
    } else {
        series = salesSummary.selected_date_hourly_totals || salesSummary.daily_hourly_totals || [];
        const selectedDate = salesSummary.selected_date || salesSummary.current_date;
        const date = new Date(`${selectedDate}T00:00:00`);
        caption = `${date.toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric"
        })} · sales by hour`;
        labelForEntry = (entry) => String(entry.hour).padStart(2, "0");
        tooltipLabelForEntry = (entry) => `${date.toLocaleDateString("en-IN", {
            day: "numeric", month: "short", year: "numeric"
        })} · ${String(entry.hour).padStart(2, "0")}:00`;
        chartLabel = `Sales by hour for ${selectedDate}`;
    }

    setText("salesRangeCaption", caption);
    setText("salesGraphTotal", currencyFormatter.format(salesSummary.completed_sales_total_all_time || 0));
    const chart = document.getElementById("salesChart");
    chart.setAttribute("aria-label", chartLabel);
    renderSalesChart("salesChart", "salesChartEmpty", series, labelForEntry, tooltipLabelForEntry);
}

function getLocalDateValue() {
    const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
}

function updateSalesPeriodPickers() {
    const range = document.querySelector('input[name="sales-range"]:checked')?.value || "day";
    document.getElementById("salesDatePicker").hidden = range !== "day";
    document.getElementById("salesMonthPicker").hidden = range !== "month";
}

async function refreshSalesChartForPeriod() {
    const status = document.getElementById("salesChartStatus");
    const requestId = ++salesChartRequest;
    const range = document.querySelector('input[name="sales-range"]:checked')?.value || "day";
    status.hidden = false;
    status.textContent = "Updating chart…";
    try {
        const summary = await getDashboardSummaryForPeriod(
            range === "day" ? document.getElementById("salesDateInput").value : undefined,
            range === "month" ? document.getElementById("salesMonthInput").value : undefined
        );
        if (requestId !== salesChartRequest) return;
        salesSummary = summary.sales;
        renderSelectedSalesRange();
        status.hidden = true;
    } catch (error) {
        if (requestId !== salesChartRequest) return;
        status.textContent = error.message || "Unable to load sales for this period.";
    }
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

        const selectedRange = document.querySelector('input[name="sales-range"]:checked')?.value || "day";
        const summary = await getDashboardSummaryForPeriod(
            selectedRange === "day" ? document.getElementById("salesDateInput").value : undefined,
            selectedRange === "month" ? document.getElementById("salesMonthInput").value : undefined
        );

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
    input.addEventListener("change", () => {
        updateSalesPeriodPickers();
        document.getElementById("salesChartStatus").hidden = true;
        if (salesSummary) {
            document.getElementById("salesChart").classList.add("is-range-switch");
            renderSelectedSalesRange();
        }
    });
});
const initialDate = getLocalDateValue();
document.getElementById("salesDateInput").value = initialDate;
document.getElementById("salesMonthInput").value = initialDate.slice(0, 7);
document.getElementById("salesDateInput").addEventListener("change", refreshSalesChartForPeriod);
document.getElementById("salesMonthInput").addEventListener("change", refreshSalesChartForPeriod);
updateSalesPeriodPickers();

if (!localStorage.getItem("access_token")) {
    window.location.href = "/";
} else {
    loadDashboard();
}
