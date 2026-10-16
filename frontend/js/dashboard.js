const loadingMessage = document.getElementById("loadingMessage");
const errorMessage = document.getElementById("errorMessage");
const dashboardContent = document.getElementById("dashboardContent");
const refreshButton = document.getElementById("refreshButton");
const logoutButton = document.getElementById("logoutButton");
const staffUsersLink = document.getElementById("staffUsersLink");

const numberFormatter = new Intl.NumberFormat("en-IN");

const currencyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
});

function setText(id, value) {
    document.getElementById(id).textContent = value;
}

async function loadDashboard() {
    loadingMessage.hidden = false;
    errorMessage.hidden = true;
    dashboardContent.hidden = true;
    refreshButton.disabled = true;

    try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        const permissions = currentUser.permissions || [];
        staffUsersLink.hidden = !(
            permissions.includes("user:read") || permissions.includes("user:write")
        );

        const summary = await apiRequest("/api/v1/dashboard/summary");

        setText(
            "activeMedicineCount",
            numberFormatter.format(summary.medicines.active_count)
        );
        setText(
            "lowStockCount",
            numberFormatter.format(summary.medicines.low_stock_count)
        );
        setText(
            "outOfStockCount",
            numberFormatter.format(summary.medicines.out_of_stock_count)
        );
        setText(
            "totalStockUnits",
            numberFormatter.format(summary.inventory.total_units)
        );
        setText(
            "inventoryValue",
            currencyFormatter.format(
                summary.inventory.purchase_cost_value
            )
        );
        setText(
            "expiredBatchCount",
            numberFormatter.format(
                summary.inventory.expired_batch_count
            )
        );
        setText(
            "expiringBatchCount",
            numberFormatter.format(
                summary.inventory.expiring_within_30_days_count
            )
        );
        setText(
            "completedBillCount",
            numberFormatter.format(
                summary.sales.completed_bill_count_all_time
            )
        );
        setText(
            "completedSalesTotal",
            currencyFormatter.format(
                summary.sales.completed_sales_total_all_time
            )
        );
        setText(
            "openPurchaseOrderCount",
            numberFormatter.format(
                summary.purchasing.open_purchase_order_count
            )
        );

        const updatedAt = new Date(summary.generated_at);
        setText(
            "updatedAt",
            `Updated ${updatedAt.toLocaleString("en-IN")}`
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

refreshButton.addEventListener("click", loadDashboard);

logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;

    try {
        await logoutUser();
        window.location.href = "/";
    } catch (error) {
        errorMessage.textContent = error.message;
        errorMessage.hidden = false;
        logoutButton.disabled = false;
    }
});

if (!localStorage.getItem("access_token")) {
    window.location.href = "/";
} else {
    loadDashboard();
}
