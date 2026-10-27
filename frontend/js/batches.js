const statusMessage = document.getElementById("statusMessage");
const errorMessage = document.getElementById("errorMessage");
const batchContent = document.getElementById("batchContent");
const batchRows = document.getElementById("batchRows");
const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const clearButton = document.getElementById("clearButton");
const refreshButton = document.getElementById("refreshButton");
const emptyMessage = document.getElementById("emptyMessage");
const noMatchesMessage = document.getElementById("noMatchesMessage");

const batchNumberFormatter = new Intl.NumberFormat("en-IN");
const batchMoneyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2
});
const batchDateFormatter = new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata"
});

function appendBatchCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.appendChild(cell);
}

function formatBatchDate(value) {
    if (!value) return "—";
    const date = new Date(`${value}T00:00:00+05:30`);
    return Number.isNaN(date.getTime()) ? "—" : batchDateFormatter.format(date);
}

function getBatchStatus(batch) {
    if (Number(batch.quantity) <= 0) return { label: "Depleted", value: "depleted" };
    if (!batch.expiry_date) return { label: "Expiry unavailable", value: "expiring" };

    const expiry = new Date(`${batch.expiry_date}T00:00:00+05:30`);
    const today = new Date();
    const todayIndia = new Date(today.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
    todayIndia.setHours(0, 0, 0, 0);
    const daysRemaining = Math.floor((expiry - todayIndia) / 86400000);

    if (daysRemaining < 0) return { label: "Expired", value: "expired" };
    if (daysRemaining <= 30) return { label: "Expiring soon", value: "expiring" };
    return { label: "Available", value: "available" };
}

function filterBatchRows() {
    const query = searchInput.value.trim().toLocaleLowerCase();
    let visibleRows = 0;

    for (const row of batchRows.querySelectorAll("tr[data-batch-row]")) {
        const matches = !query || row.dataset.searchText.includes(query);
        row.hidden = !matches;
        if (matches) visibleRows += 1;
    }

    noMatchesMessage.hidden = !query || visibleRows > 0 || emptyMessage.hidden === false;
}

function renderBatches(batches, medicineNames) {
    batchRows.replaceChildren();
    let totalUnits = 0;

    for (const batch of batches) {
        const row = document.createElement("tr");
        row.dataset.batchRow = "true";
        const status = getBatchStatus(batch);
        const medicineName = medicineNames.get(batch.medicine_id) || "Unknown medicine";
        row.dataset.searchText = [medicineName, batch.batch_number, status.label]
            .join(" ")
            .toLocaleLowerCase();

        appendBatchCell(row, medicineName);
        appendBatchCell(row, batch.batch_number || "—");
        appendBatchCell(row, batchNumberFormatter.format(Number(batch.quantity) || 0));
        appendBatchCell(row, batchMoneyFormatter.format(Number(batch.purchase_price) || 0));
        appendBatchCell(row, formatBatchDate(batch.manufacturing_date));
        appendBatchCell(row, formatBatchDate(batch.expiry_date));

        const statusCell = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = "batch-status";
        badge.dataset.status = status.value;
        badge.textContent = status.label;
        statusCell.appendChild(badge);
        row.appendChild(statusCell);
        batchRows.appendChild(row);
        totalUnits += Math.max(Number(batch.quantity) || 0, 0);
    }

    document.getElementById("batchCount").textContent = batchNumberFormatter.format(batches.length);
    document.getElementById("unitCount").textContent = batchNumberFormatter.format(totalUnits);
    emptyMessage.hidden = batches.length > 0;
    filterBatchRows();
}

async function loadBatches() {
    refreshButton.disabled = true;
    statusMessage.textContent = "Loading stock batches…";
    statusMessage.hidden = false;
    errorMessage.hidden = true;
    batchContent.hidden = true;

    try {
        const currentUser = await getCurrentUser();
        if (!(currentUser.permissions || []).includes("stock:read")) {
            throw new Error("You do not have permission to view stock batches.");
        }

        const pageSize = 100;
        const firstPage = await apiRequest(`/api/v1/medicines?page=1&limit=${pageSize}&is_active=true`);
        const pageCount = Math.ceil(firstPage.total / pageSize);
        const remainingPages = await Promise.all(
            Array.from({ length: Math.max(pageCount - 1, 0) }, (_, index) =>
                apiRequest(`/api/v1/medicines?page=${index + 2}&limit=${pageSize}&is_active=true`)
            )
        );
        const medicines = [firstPage, ...remainingPages].flatMap((page) => page.items);
        const medicineNames = new Map(medicines.map((medicine) => [medicine.id, medicine.name]));
        const batches = await apiRequest("/api/v1/stock-batches");

        renderBatches(batches, medicineNames);
        statusMessage.hidden = true;
        batchContent.hidden = false;
    } catch (error) {
        statusMessage.hidden = true;
        errorMessage.textContent = error.message || "Unable to load stock batches.";
        errorMessage.hidden = false;
    } finally {
        refreshButton.disabled = false;
    }
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    filterBatchRows();
});

searchInput.addEventListener("input", filterBatchRows);
clearButton.addEventListener("click", () => {
    searchInput.value = "";
    filterBatchRows();
    searchInput.focus();
});
refreshButton.addEventListener("click", loadBatches);

loadBatches();
