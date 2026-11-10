const reportCurrency = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const reportNumber = new Intl.NumberFormat("en-IN");
const reportRange = document.getElementById("reportRange");
const reportTrendChart = document.getElementById("reportTrendChart");
let reportData = null;
let reportChartRequest = 0;

function reportLocalDate() {
    const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
}

function updateReportPeriodPickers() {
    document.getElementById("reportDatePicker").hidden = reportRange.value !== "day";
    document.getElementById("reportMonthPicker").hidden = reportRange.value !== "month";
}

function reportText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function renderReportTrend() {
    if (!reportData) return;
    const range = reportRange.value;
    const sales = reportData.sales;
    const series = range === "month" ? (sales.selected_month_daily_totals || sales.monthly_daily_totals) : range === "year" ? sales.yearly_totals : (sales.selected_date_hourly_totals || sales.daily_hourly_totals);
    const label = range === "month" ? (entry) => entry.day : range === "year" ? (entry) => entry.year : (entry) => String(entry.hour).padStart(2, "0");
    const hasValues = series.some((entry) => entry.total_amount > 0 || entry.purchase_amount > 0);
    reportTrendChart.replaceChildren();
    reportTrendChart.hidden = !hasValues;
    document.getElementById("reportTrendEmpty").hidden = hasValues;
    reportText("reportRangeCaption", range === "month" ? `${sales.selected_month || sales.current_month} · daily totals` : range === "year" ? "Annual totals" : `${new Date(`${sales.selected_date || sales.current_date}T00:00:00`).toLocaleDateString("en-IN")} · hourly totals`);
    if (!hasValues) return;

    const svgNS = "http://www.w3.org/2000/svg";
    const width = 1000, height = 300, left = 65, right = 18, top = 20, bottom = 40;
    const plotW = width - left - right, plotH = height - top - bottom;
    const maximum = Math.max(1, ...series.flatMap((entry) => [entry.total_amount || 0, entry.purchase_amount || 0]));
    const axisMax = Math.ceil(maximum / 4 / 100) * 100 * 4 || 1;
    const step = axisMax / 4;
    const pointsFor = (key) => series.map((entry, index) => ({
        x: left + (series.length === 1 ? plotW / 2 : index / (series.length - 1) * plotW),
        y: top + plotH - (entry[key] || 0) / axisMax * plotH,
        value: entry[key] || 0,
        label: label(entry)
    }));
    const salesPoints = pointsFor("total_amount"), purchasePoints = pointsFor("purchase_amount");
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");

    for (let tick = 0; tick <= 4; tick++) {
        const y = top + plotH / 4 * tick;
        const grid = document.createElementNS(svgNS, "line");
        grid.setAttribute("x1", left); grid.setAttribute("x2", width - right); grid.setAttribute("y1", y); grid.setAttribute("y2", y); grid.setAttribute("class", "report-grid-line"); svg.append(grid);
        const text = document.createElementNS(svgNS, "text");
        text.setAttribute("x", left - 9); text.setAttribute("y", y + 4); text.setAttribute("text-anchor", "end"); text.setAttribute("class", "report-axis-label"); text.textContent = reportNumber.format(axisMax - step * tick); svg.append(text);
    }

    const makePath = (points) => points.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" ");
    const isDark = document.documentElement.dataset.theme === "dark";
    [[salesPoints, isDark ? "#22b9b5" : "#0b9c9d", "report-sales-line"], [purchasePoints, isDark ? "#c4d2e8" : "#94a3b8", "report-purchases-line"]].forEach(([points, color, className]) => {
        const path = document.createElementNS(svgNS, "path");
        path.setAttribute("d", makePath(points)); path.setAttribute("fill", "none"); path.setAttribute("stroke", color); path.setAttribute("stroke-width", className === "report-sales-line" ? "3" : "2.5");
        if (className === "report-purchases-line") path.setAttribute("stroke-dasharray", "6 5");
        svg.append(path);
        points.forEach((point) => {
            const circle = document.createElementNS(svgNS, "circle"); circle.setAttribute("cx", point.x); circle.setAttribute("cy", point.y); circle.setAttribute("r", "4.5"); circle.setAttribute("fill", color); circle.setAttribute("class", "report-chart-point"); circle.setAttribute("tabindex", "0");
            const title = document.createElementNS(svgNS, "title"); title.textContent = `${className === "report-sales-line" ? "Revenue" : "Received purchases"} · ${point.label}: ${reportCurrency.format(point.value)}`; circle.append(title); svg.append(circle);
        });
    });
    const stride = Math.max(1, Math.ceil(series.length / 10));
    salesPoints.forEach((point, index) => {
        if (index % stride && index !== salesPoints.length - 1) return;
        const text = document.createElementNS(svgNS, "text"); text.setAttribute("x", point.x); text.setAttribute("y", height - 8); text.setAttribute("text-anchor", "middle"); text.setAttribute("class", "report-axis-label"); text.textContent = point.label; svg.append(text);
    });
    reportTrendChart.append(svg);
}

async function refreshReportTrendForPeriod() {
    if (!reportData) return;
    const status = document.getElementById("reportTrendStatus");
    const requestId = ++reportChartRequest;
    status.hidden = false;
    status.textContent = "Updating chart…";
    try {
        const range = reportRange.value;
        const summary = await getDashboardSummaryForPeriod(
            range === "day" ? document.getElementById("reportDateInput").value : undefined,
            range === "month" ? document.getElementById("reportMonthInput").value : undefined
        );
        if (requestId !== reportChartRequest) return;
        reportData.sales = summary.sales;
        renderReportTrend();
        status.hidden = true;
    } catch (error) {
        if (requestId !== reportChartRequest) return;
        status.textContent = error.message || "Unable to load sales for this period.";
    }
}

function renderReportDetails() {
    const list = document.getElementById("reportTopMedicines");
    list.replaceChildren();
    const top = reportData.top_selling_medicines || [];
    document.getElementById("reportTopEmpty").hidden = top.length > 0;
    top.forEach((medicine, index) => {
        const row = document.createElement("div"); row.className = "report-record-row";
        const name = document.createElement("strong"); name.textContent = `${String(index + 1).padStart(2, "0")} · ${medicine.medicine_name}`;
        const details = document.createElement("span"); details.textContent = `${reportNumber.format(medicine.units_sold)} units · ${reportCurrency.format(medicine.revenue)}`;
        row.append(name, details); list.append(row);
    });

    const categories = document.getElementById("reportCategories"); categories.replaceChildren();
    const categoryRows = reportData.category_distribution || [];
    document.getElementById("reportCategoriesEmpty").hidden = categoryRows.length > 0;
    categoryRows.forEach((category) => {
        const row = document.createElement("div"); row.className = "report-category-row";
        const labels = document.createElement("div"); labels.className = "report-category-labels";
        const name = document.createElement("strong"); name.textContent = category.category_name;
        const amount = document.createElement("span"); amount.textContent = `${category.percentage}% · ${reportCurrency.format(category.stock_value)}`; labels.append(name, amount);
        const track = document.createElement("div"); track.className = "report-category-track";
        const bar = document.createElement("span"); bar.style.width = `${Math.max(0, Math.min(category.percentage, 100))}%`; track.append(bar);
        row.append(labels, track); categories.append(row);
    });
}

async function loadReports() {
    const loading = document.getElementById("reportsLoading"), error = document.getElementById("reportsError"), body = document.getElementById("reportsBody"), refresh = document.getElementById("reportsRefresh");
    loading.hidden = false; error.hidden = true; body.hidden = true; refresh.disabled = true;
    try {
        const range = reportRange.value;
        reportData = await getDashboardSummaryForPeriod(
            range === "day" ? document.getElementById("reportDateInput").value : undefined,
            range === "month" ? document.getElementById("reportMonthInput").value : undefined
        );
        const { sales, inventory, medicines, purchasing } = reportData;
        reportText("reportTodayRevenue", reportCurrency.format(sales.daily_sales_total));
        reportText("reportTodayBills", `${reportNumber.format(sales.daily_completed_bill_count)} completed bills today`);
        reportText("reportMonthRevenue", reportCurrency.format(sales.monthly_sales_total));
        reportText("reportMonthPurchases", `${reportCurrency.format(sales.monthly_purchase_total)} received purchases this month`);
        reportText("reportAllSales", reportCurrency.format(sales.completed_sales_total_all_time));
        reportText("reportAllPurchases", `${reportCurrency.format(purchasing.received_purchase_total_all_time)} received purchases all time`);
        reportText("reportStockValue", reportCurrency.format(inventory.purchase_cost_value));
        reportText("reportStockUnits", `${reportNumber.format(inventory.total_units)} units in batches · ${medicines.active_count} active SKUs`);
        reportText("reportUpdatedAt", `Updated ${new Date(reportData.generated_at).toLocaleString("en-IN")}`);
        renderReportDetails(); renderReportTrend();
        loading.hidden = true; body.hidden = false;
    } catch (caught) {
        loading.hidden = true; error.textContent = caught.message; error.hidden = false;
    } finally { refresh.disabled = false; }
}

reportRange.addEventListener("change", () => { updateReportPeriodPickers(); refreshReportTrendForPeriod(); });
const reportInitialDate = reportLocalDate();
document.getElementById("reportDateInput").value = reportInitialDate;
document.getElementById("reportMonthInput").value = reportInitialDate.slice(0, 7);
document.getElementById("reportDateInput").addEventListener("change", refreshReportTrendForPeriod);
document.getElementById("reportMonthInput").addEventListener("change", refreshReportTrendForPeriod);
updateReportPeriodPickers();
document.getElementById("reportsRefresh").addEventListener("click", loadReports);
loadReports();
