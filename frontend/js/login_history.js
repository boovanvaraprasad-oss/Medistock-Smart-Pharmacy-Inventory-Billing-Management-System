const historyStatus = document.getElementById("statusMessage");
const historyError = document.getElementById("errorMessage");
const historyRows = document.getElementById("loginRows");
const historyFilter = document.getElementById("resultFilter");
const historyPageSize = 25;
let historyPage = 1;
let historyTotal = 0;

function appendHistoryCell(row, text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) cell.className = className;
    row.append(cell);
    return cell;
}

function formatHistoryTime(value) {
    if (!value) return { date: "—", time: "—" };
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return { date: "—", time: "—" };
    return {
        date: new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeZone: "Asia/Kolkata" }).format(date),
        time: new Intl.DateTimeFormat("en-IN", { timeStyle: "medium", timeZone: "Asia/Kolkata" }).format(date)
    };
}

function browserLabel(userAgent) {
    if (!userAgent) return "—";
    if (/Edg\//.test(userAgent)) return "Microsoft Edge";
    if (/Firefox\//.test(userAgent)) return "Firefox";
    if (/Chrome\//.test(userAgent)) return "Chrome";
    if (/Safari\//.test(userAgent)) return "Safari";
    return "Other browser";
}

function renderLoginRows(items) {
    historyRows.replaceChildren();
    document.getElementById("emptyMessage").hidden = items.length > 0;
    for (const entry of items) {
        const row = document.createElement("tr");
        appendHistoryCell(row, entry.email || "Unknown account");
        appendHistoryCell(row, entry.role
            ? entry.role.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
            : "Unknown");
        const time = formatHistoryTime(entry.timestamp);
        appendHistoryCell(row, time.date);
        appendHistoryCell(row, time.time);
        const result = appendHistoryCell(row, entry.success ? "Successful" : "Failed", `history-result ${entry.success ? "result-success" : "result-failed"}`);
        result.setAttribute("aria-label", `Login ${entry.success ? "successful" : "failed"}`);
        appendHistoryCell(row, entry.ip_address || "—");
        const browser = appendHistoryCell(row, browserLabel(entry.user_agent));
        if (entry.user_agent) browser.title = entry.user_agent;
        historyRows.append(row);
    }
}

async function loadLoginHistory() {
    historyStatus.hidden = false;
    historyStatus.textContent = "Loading login history…";
    historyError.hidden = true;
    document.getElementById("refreshButton").disabled = true;
    try {
        const user = await getCurrentUser();
        if (!["owner", "store_manager"].includes(user.role)) {
            window.location.replace(getDashboardForRole(user.role));
            return;
        }
        const params = new URLSearchParams({ page: String(historyPage), limit: String(historyPageSize) });
        if (historyFilter.value !== "") params.set("success", historyFilter.value);
        const data = await apiRequest(`/api/v1/auth/login-logs?${params}`);
        historyTotal = data.total;
        renderLoginRows(data.items);
        document.getElementById("resultCount").textContent = new Intl.NumberFormat("en-IN").format(historyTotal);
        const pageCount = Math.max(1, Math.ceil(historyTotal / historyPageSize));
        document.getElementById("pageLabel").textContent = `Page ${historyPage} of ${pageCount}`;
        document.getElementById("previousPage").disabled = historyPage <= 1;
        document.getElementById("nextPage").disabled = historyPage >= pageCount;
        historyStatus.hidden = true;
    } catch (error) {
        historyStatus.hidden = true;
        historyError.textContent = error.message || "Unable to load login history.";
        historyError.hidden = false;
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    } finally {
        document.getElementById("refreshButton").disabled = false;
    }
}

document.getElementById("refreshButton").addEventListener("click", loadLoginHistory);
document.getElementById("previousPage").addEventListener("click", () => { if (historyPage > 1) { historyPage -= 1; loadLoginHistory(); } });
document.getElementById("nextPage").addEventListener("click", () => { if (historyPage * historyPageSize < historyTotal) { historyPage += 1; loadLoginHistory(); } });
historyFilter.addEventListener("change", () => { historyPage = 1; loadLoginHistory(); });
loadLoginHistory();
