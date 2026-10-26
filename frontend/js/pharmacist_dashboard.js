const statusMessage = document.getElementById("statusMessage");
const errorMessage = document.getElementById("errorMessage");
const dashboardContent = document.getElementById("dashboardContent");
const refreshButton = document.getElementById("refreshButton");
const lowStockRows = document.getElementById("lowStockRows");
const lowStockEmpty = document.getElementById("lowStockEmpty");
const recentBills = document.getElementById("recentBills");
const recentBillsEmpty = document.getElementById("recentBillsEmpty");

const numberFormatter = new Intl.NumberFormat("en-IN");
const currencyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
});

function addCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.appendChild(cell);
}

function renderLowStock(medicines) {
    const lowStock = medicines
        .filter((medicine) =>
            medicine.is_active &&
            Number(medicine.stock ?? 0) <= Number(medicine.reorder_threshold ?? 10)
        )
        .slice(0, 6);

    lowStockRows.replaceChildren();
    lowStockEmpty.hidden = lowStock.length !== 0;

    for (const medicine of lowStock) {
        const row = document.createElement("tr");
        addCell(row, medicine.name || "—");
        addCell(row, medicine.sku || "—");
        addCell(row, numberFormatter.format(medicine.stock ?? 0));
        addCell(row, numberFormatter.format(medicine.reorder_threshold ?? 10));
        lowStockRows.appendChild(row);
    }
}

function renderRecentBills(bills) {
    const latestBills = bills.slice(0, 6);

    recentBills.replaceChildren();
    recentBillsEmpty.hidden = latestBills.length !== 0;

    for (const bill of latestBills) {
        const row = document.createElement("article");
        row.className = "recent-bill";

        const details = document.createElement("span");
        const invoice = document.createElement("strong");
        invoice.textContent = bill.invoice_number || "Invoice";
        const customer = document.createElement("small");
        customer.textContent = bill.customer_name || "Walk-in customer";
        const status = document.createElement("span");
        status.className = "bill-status-pill";
        status.dataset.status = bill.status || "draft";
        status.textContent = bill.status || "Draft";

        details.append(invoice, customer, status);

        const amount = document.createElement("span");
        amount.className = "bill-amount";
        amount.textContent = currencyFormatter.format(Number(bill.total_amount || 0));

        row.append(details, amount);
        recentBills.appendChild(row);
    }
}

async function loadDashboard() {
    statusMessage.textContent = "Loading your dashboard…";
    statusMessage.hidden = false;
    errorMessage.hidden = true;
    dashboardContent.hidden = true;
    refreshButton.disabled = true;

    try {
        const currentUser = await getCurrentUser();
        const correctDashboard = getDashboardForRole(currentUser.role);
        if (correctDashboard !== "pharmacist_dashboard.html") {
            window.location.replace(correctDashboard);
            return;
        }

        const [medicineResponse, bills] = await Promise.all([
            apiRequest("/api/v1/medicines?page=1&limit=100&is_active=true"),
            apiRequest("/api/v1/bills")
        ]);

        const completedBills = bills.filter((bill) => bill.status === "completed");
        const draftBills = bills.filter((bill) => bill.status === "draft");

        document.getElementById("activeMedicineCount").textContent =
            numberFormatter.format(medicineResponse.total);
        document.getElementById("completedBillCount").textContent =
            numberFormatter.format(completedBills.length);
        document.getElementById("draftBillCount").textContent =
            numberFormatter.format(draftBills.length);

        renderLowStock(medicineResponse.items);
        renderRecentBills(bills);

        statusMessage.hidden = true;
        dashboardContent.hidden = false;
    } catch (error) {
        statusMessage.hidden = true;
        errorMessage.textContent = error.message || "Unable to load your dashboard.";
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
