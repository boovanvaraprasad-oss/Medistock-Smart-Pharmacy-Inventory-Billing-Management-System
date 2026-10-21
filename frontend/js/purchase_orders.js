const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const statusMessage = document.getElementById("statusMessage");
const listDescription = document.getElementById("listDescription");
const orderRows = document.getElementById("orderRows");
const createOrderSection = document.getElementById("createOrderSection");
const createOrderForm = document.getElementById("createOrderForm");
const supplierSelect = document.getElementById("supplierSelect");
const orderNotes = document.getElementById("orderNotes");
const createOrderButton = document.getElementById("createOrderButton");
const refreshButton = document.getElementById("refreshButton");

const orderDetailsSection = document.getElementById("orderDetailsSection");
const selectedOrderTitle = document.getElementById("selectedOrderTitle");
const selectedOrderDescription = document.getElementById("selectedOrderDescription");
const closeDetailsButton = document.getElementById("closeDetailsButton");
const addItemSection = document.getElementById("addItemSection");
const itemForm = document.getElementById("itemForm");
const medicineSelect = document.getElementById("medicineSelect");
const itemQuantity = document.getElementById("itemQuantity");
const itemPrice = document.getElementById("itemPrice");
const itemBatchNumber = document.getElementById("itemBatchNumber");
const itemManufacturingDate = document.getElementById("itemManufacturingDate");
const itemExpiryDate = document.getElementById("itemExpiryDate");
const addItemButton = document.getElementById("addItemButton");
const itemsMessage = document.getElementById("itemsMessage");
const itemRows = document.getElementById("itemRows");

let permissions = [];
let suppliers = [];
let medicines = [];
let orders = [];
let purchaseItems = [];
let selectedOrder = null;

function showMessage(element, message) {
    element.textContent = message;
    element.hidden = !message;
}

function makeButton(label, className, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
}

function addCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value ?? "—";
    row.appendChild(cell);
    return cell;
}

function supplierName(supplierId) {
    const supplier = suppliers.find((item) => item.id === supplierId);
    return supplier ? supplier.name : "Unknown supplier";
}

function medicineName(medicineId) {
    const medicine = medicines.find((item) => item.id === medicineId);
    return medicine ? medicine.name : "Unknown medicine";
}

function formatMoney(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR"
    }).format(Number(value) || 0);
}

function setSelectOptions(select, records, placeholder, getLabel) {
    select.replaceChildren();

    const firstOption = document.createElement("option");
    firstOption.value = "";
    firstOption.textContent = placeholder;
    firstOption.disabled = true;
    firstOption.selected = true;
    select.appendChild(firstOption);

    for (const record of records) {
        const option = document.createElement("option");
        option.value = record.id;
        option.textContent = getLabel(record);
        select.appendChild(option);
    }

    select.disabled = records.length === 0;
}

function renderOrders() {
    orderRows.replaceChildren();

    if (orders.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.textContent = "No purchase orders found.";
        row.appendChild(cell);
        orderRows.appendChild(row);
        return;
    }

    for (const order of orders) {
        const row = document.createElement("tr");
        addCell(row, supplierName(order.supplier_id));

        const statusCell = document.createElement("td");
        const status = document.createElement("span");
        status.className = "order-status";
        status.dataset.status = order.status;
        status.textContent = order.status;
        statusCell.appendChild(status);
        row.appendChild(statusCell);

        addCell(row, order.notes || "—");

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "order-actions";

        actions.appendChild(makeButton(
            "View items",
            "button button-secondary button-small",
            () => openOrder(order)
        ));

        if (
            permissions.includes("purchase:write") &&
            order.status === "draft"
        ) {
            actions.appendChild(makeButton(
                "Mark ordered",
                "button button-secondary button-small",
                () => updateOrderStatus(order, "ordered")
            ));
        }

        if (
            permissions.includes("purchase:write") &&
            ["draft", "ordered"].includes(order.status)
        ) {
            actions.appendChild(makeButton(
                "Cancel order",
                "button button-secondary button-small",
                () => updateOrderStatus(order, "cancelled")
            ));
        }

        if (
            permissions.includes("purchase:write") &&
            ["draft", "ordered"].includes(order.status)
        ) {
            actions.appendChild(makeButton(
                "Receive stock",
                "button button-primary button-small",
                () => receiveOrder(order)
            ));
        }

        actionsCell.appendChild(actions);
        row.appendChild(actionsCell);
        orderRows.appendChild(row);
    }
}

function renderItems() {
    itemRows.replaceChildren();

    const orderItems = purchaseItems.filter(
        (item) => item.purchase_order_id === selectedOrder?.id
    );

    itemsMessage.textContent = orderItems.length
        ? `${orderItems.length} batch item${orderItems.length === 1 ? "" : "s"} on this order.`
        : "No items have been added to this order yet.";
    itemsMessage.hidden = false;

    if (orderItems.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.textContent = "No items found.";
        row.appendChild(cell);
        itemRows.appendChild(row);
        return;
    }

    for (const item of orderItems) {
        const row = document.createElement("tr");
        addCell(row, medicineName(item.medicine_id));
        addCell(row, item.batch_number || "—");
        addCell(row, item.quantity);
        addCell(row, formatMoney(item.unit_price));
        addCell(row, formatMoney(item.total_price));
        addCell(row, item.expiry_date || "—");
        itemRows.appendChild(row);
    }
}

async function loadOrders() {
    statusMessage.textContent = "Loading purchase orders…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        const [loadedOrders, loadedItems] = await Promise.all([
            apiRequest("/api/v1/purchase-orders"),
            apiRequest("/api/v1/purchase-items")
        ]);

        orders = loadedOrders;
        purchaseItems = loadedItems;
        renderOrders();

        listDescription.textContent = `${orders.length} purchase order${orders.length === 1 ? "" : "s"}`;
        statusMessage.textContent = orders.length ? "" : "No purchase orders found.";
        statusMessage.hidden = orders.length > 0;

        if (selectedOrder) {
            selectedOrder = orders.find((order) => order.id === selectedOrder.id) || null;
            if (selectedOrder) {
                updateOrderDetails();
            } else {
                orderDetailsSection.hidden = true;
            }
        }
    } catch (error) {
        statusMessage.hidden = true;
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

function openOrder(order) {
    selectedOrder = order;
    orderDetailsSection.hidden = false;
    updateOrderDetails();
    orderDetailsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateOrderDetails() {
    if (!selectedOrder) {
        orderDetailsSection.hidden = true;
        return;
    }

    selectedOrderTitle.textContent = `Order for ${supplierName(selectedOrder.supplier_id)}`;
    selectedOrderDescription.textContent =
        `Status: ${selectedOrder.status}${selectedOrder.notes ? ` · ${selectedOrder.notes}` : ""}`;

    const canEdit = permissions.includes("purchase:write") &&
        ["draft", "ordered"].includes(selectedOrder.status);

    addItemSection.hidden = !canEdit;
    renderItems();
}

async function updateOrderStatus(order, newStatus) {
    const message = newStatus === "cancelled"
        ? "Cancel this purchase order?"
        : "Mark this purchase order as ordered?";

    if (!window.confirm(message)) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(
            `/api/v1/purchase-orders/${encodeURIComponent(order.id)}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: newStatus })
            }
        );

        showMessage(successMessage, `Purchase order ${newStatus}.`);
        await loadOrders();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

async function receiveOrder(order) {
    const itemCount = purchaseItems.filter(
        (item) => item.purchase_order_id === order.id
    ).length;

    if (itemCount === 0) {
        showMessage(errorMessage, "Add at least one batch item before receiving this order.");
        return;
    }

    const confirmed = window.confirm(
        `Receive this order with ${itemCount} batch item${itemCount === 1 ? "" : "s"}? This will add the quantities to stock and cannot be undone.`
    );

    if (!confirmed) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(
            `/api/v1/purchase-orders/${encodeURIComponent(order.id)}/receive`,
            { method: "PATCH" }
        );

        showMessage(
            successMessage,
            "Order received. Stock batches and stock transactions have been recorded."
        );
        await loadOrders();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

createOrderForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    createOrderButton.disabled = true;

    try {
        const createdOrder = await apiRequest("/api/v1/purchase-orders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                supplier_id: supplierSelect.value,
                notes: orderNotes.value.trim() || null
            })
        });

        createOrderForm.reset();
        showMessage(successMessage, "Draft purchase order created.");
        await loadOrders();
        const refreshedOrder = orders.find((order) => order.id === createdOrder.id);
        if (refreshedOrder) {
            openOrder(refreshedOrder);
        }
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        createOrderButton.disabled = false;
    }
});

itemForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedOrder) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    addItemButton.disabled = true;

    const requestBody = {
        purchase_order_id: selectedOrder.id,
        medicine_id: medicineSelect.value,
        quantity: Number(itemQuantity.value),
        unit_price: Number(itemPrice.value),
        batch_number: itemBatchNumber.value.trim(),
        expiry_date: itemExpiryDate.value
    };

    if (itemManufacturingDate.value) {
        requestBody.manufacturing_date = itemManufacturingDate.value;
    }

    try {
        await apiRequest("/api/v1/purchase-items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        itemForm.reset();
        showMessage(successMessage, "Batch item added to the purchase order.");
        await loadOrders();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        addItemButton.disabled = false;
    }
});

refreshButton.addEventListener("click", loadOrders);

closeDetailsButton.addEventListener("click", () => {
    selectedOrder = null;
    orderDetailsSection.hidden = true;
});

async function initializePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        permissions = currentUser.permissions || [];

        if (!permissions.includes("purchase:read")) {
            showMessage(errorMessage, "Your account does not have permission to view purchase orders.");
            statusMessage.hidden = true;
            return;
        }

        const [loadedSuppliers, medicineResponse] = await Promise.all([
            apiRequest("/api/v1/suppliers"),
            apiRequest("/api/v1/medicines?page=1&limit=100&is_active=true")
        ]);

        suppliers = loadedSuppliers.filter((supplier) => supplier.is_active);
        medicines = medicineResponse.items.filter((medicine) => medicine.is_active);

        setSelectOptions(
            supplierSelect,
            suppliers,
            suppliers.length ? "Choose a supplier" : "No active suppliers available",
            (supplier) => supplier.name
        );

        setSelectOptions(
            medicineSelect,
            medicines,
            medicines.length ? "Choose a medicine" : "No active medicines available",
            (medicine) => `${medicine.name}${medicine.sku ? ` (${medicine.sku})` : ""}`
        );

        if (permissions.includes("purchase:write")) {
            createOrderSection.hidden = false;
        }

        await loadOrders();
    } catch (error) {
        showMessage(errorMessage, error.message);
        statusMessage.hidden = true;

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();