const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const statusMessage = document.getElementById("statusMessage");
const billListDescription = document.getElementById("billListDescription");
const billRows = document.getElementById("billRows");
const createBillSection = document.getElementById("createBillSection");
const createBillForm = document.getElementById("createBillForm");
const customerNameInput = document.getElementById("customerName");
const customerPhoneInput = document.getElementById("customerPhone");
const createBillButton = document.getElementById("createBillButton");
const refreshButton = document.getElementById("refreshButton");
const batchReturnActionsHeading = document.getElementById("batchReturnActionsHeading");

const billDetailsSection = document.getElementById("billDetailsSection");
const billDetailsTitle = document.getElementById("billDetailsTitle");
const billDetailsDescription = document.getElementById("billDetailsDescription");
const closeDetailsButton = document.getElementById("closeDetailsButton");
const printInvoiceButton = document.getElementById("printInvoiceButton");
const addBillItemSection = document.getElementById("addBillItemSection");
const addBillItemForm = document.getElementById("addBillItemForm");
const medicineSearchInput = document.getElementById("medicineSearch");
const medicineSearchStatus = document.getElementById("medicineSearchStatus");
const medicineSelect = document.getElementById("medicineSelect");
const quantityInput = document.getElementById("quantity");
const addItemButton = document.getElementById("addItemButton");
const billItemRows = document.getElementById("billItemRows");
const itemActionsHeading = document.getElementById("itemActionsHeading");
const billSubtotal = document.getElementById("billSubtotal");
const billTax = document.getElementById("billTax");
const billTotal = document.getElementById("billTotal");
const billCompletionActions = document.getElementById("billCompletionActions");
const billApprovalMessage = document.getElementById("billApprovalMessage");
const billCompletionMessage = document.getElementById("billCompletionMessage");
const completeBillButton = document.getElementById("completeBillButton");
const paymentMethodInput = document.getElementById("paymentMethod");
const amountReceivedInput = document.getElementById("amountReceived");
const batchAllocationsSection = document.getElementById("batchAllocationsSection");
const batchAllocationRows = document.getElementById("batchAllocationRows");

let permissions = [];
let bills = [];
let medicines = [];
let selectedBill = null;
let medicineSearchTimer = null;
let medicineSearchRequestId = 0;

const paymentSummary = document.createElement("div");
paymentSummary.className = "bill-totals bill-payment-summary";
paymentSummary.hidden = true;

const paymentSummaryRows = {};
for (const label of ["Payment method", "Amount received", "Change due"]) {
    const row = document.createElement("p");
    const value = document.createElement("strong");
    row.append(document.createTextNode(`${label} `), value);
    paymentSummary.appendChild(row);
    paymentSummaryRows[label] = { row, value };
}
billTotal.closest(".bill-totals").insertAdjacentElement("afterend", paymentSummary);

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

function formatMoney(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR"
    }).format(Number(value) || 0);
}

function paymentMethodLabel(method) {
    const labels = {
        cash: "Cash",
        card: "Card",
        upi: "UPI"
    };
    return labels[String(method || "").toLowerCase()] || "—";
}

function renderPaymentSummary() {
    const isCompleted = selectedBill?.status === "completed";
    paymentSummary.hidden = !isCompleted;

    if (!isCompleted) {
        return;
    }

    paymentSummaryRows["Payment method"].value.textContent =
        paymentMethodLabel(selectedBill.payment_method);
    paymentSummaryRows["Amount received"].value.textContent =
        formatMoney(selectedBill.amount_received);
    paymentSummaryRows["Change due"].value.textContent =
        formatMoney(selectedBill.change_due);

    paymentSummaryRows["Change due"].row.hidden =
        Number(selectedBill.change_due || 0) <= 0;
}

function renderMedicineOptions(records, total = records.length) {
    medicineSelect.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = records.length
        ? "Choose a medicine"
        : "No matching medicines";
    placeholder.disabled = true;
    placeholder.selected = true;
    medicineSelect.appendChild(placeholder);

    for (const medicine of records) {
        const option = document.createElement("option");
        option.value = medicine.id;
        option.textContent =
            `${medicine.name} · ${medicine.stock} in stock · ${formatMoney(medicine.price)}`;
        medicineSelect.appendChild(option);
    }

    medicineSelect.disabled = records.length === 0;
    if (total > records.length) {
        medicineSearchStatus.textContent =
            `Showing ${records.length} of ${total} matches. Type more letters to narrow the results.`;
    } else {
        medicineSearchStatus.textContent = records.length
            ? `${total} matching medicine${total === 1 ? "" : "s"}.`
            : "No active medicines match that name.";
    }
}

async function searchMedicines(query, requestId) {
    const parameters = new URLSearchParams({
        page: "1",
        limit: "100",
        is_active: "true"
    });
    if (query) parameters.set("search", query);

    medicineSelect.disabled = true;
    medicineSelect.replaceChildren();
    const loadingOption = document.createElement("option");
    loadingOption.value = "";
    loadingOption.textContent = "Searching medicines…";
    loadingOption.selected = true;
    medicineSelect.appendChild(loadingOption);
    medicineSearchStatus.textContent = "Searching medicines…";

    try {
        const response = await apiRequest(`/api/v1/medicines?${parameters.toString()}`);
        if (requestId !== medicineSearchRequestId) return;

        medicines = response.items.filter((medicine) => medicine.is_active);
        renderMedicineOptions(medicines, response.total);
    } catch (error) {
        if (requestId !== medicineSearchRequestId) return;
        medicines = [];
        medicineSelect.replaceChildren();
        const failedOption = document.createElement("option");
        failedOption.value = "";
        failedOption.textContent = "Search unavailable";
        failedOption.selected = true;
        medicineSelect.appendChild(failedOption);
        medicineSelect.disabled = true;
        medicineSearchStatus.textContent = error.message || "Unable to search medicines.";
    }
}

function scheduleMedicineSearch(query) {
    window.clearTimeout(medicineSearchTimer);
    const requestId = ++medicineSearchRequestId;
    medicineSelect.value = "";
    medicineSelect.disabled = true;
    quantityInput.removeAttribute("max");
    medicineSearchStatus.textContent = "Waiting to search…";
    medicineSearchTimer = window.setTimeout(
        () => searchMedicines(query.trim(), requestId),
        250
    );
}

function renderBills() {
    billRows.replaceChildren();

    if (bills.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.textContent = "No bills found.";
        row.appendChild(cell);
        billRows.appendChild(row);
        return;
    }

    for (const bill of bills) {
        const row = document.createElement("tr");
        addCell(row, bill.invoice_number);
        addCell(row, bill.customer_name);
        addCell(row, formatMoney(bill.total_amount));

        const paymentText = bill.payment_method
            ? `${bill.payment_status} · ${paymentMethodLabel(bill.payment_method)}`
            : bill.payment_status;
        addCell(row, paymentText);

        const statusCell = document.createElement("td");
        const status = document.createElement("span");
        status.className = "bill-status";
        status.dataset.status = bill.status;
        status.textContent = bill.status;
        statusCell.appendChild(status);
        row.appendChild(statusCell);

        const actionCell = document.createElement("td");
        actionCell.appendChild(makeButton(
            "View",
            "button button-secondary button-small",
            () => openBill(bill.id)
        ));
        row.appendChild(actionCell);

        billRows.appendChild(row);
    }
}

async function loadBills() {
    statusMessage.textContent = "Loading bills…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        bills = await apiRequest("/api/v1/bills");
        renderBills();

        billListDescription.textContent =
            `${bills.length} bill${bills.length === 1 ? "" : "s"}`;
        statusMessage.textContent = bills.length ? "" : "No bills found.";
        statusMessage.hidden = bills.length > 0;

        if (selectedBill) {
            const stillExists = bills.some((bill) => bill.id === selectedBill.id);
            if (stillExists) {
                await openBill(selectedBill.id, false);
            } else {
                selectedBill = null;
                billDetailsSection.hidden = true;
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

async function openBill(billId, scroll = true) {
    showMessage(errorMessage, "");
    if (selectedBill?.id !== billId) {
        showMessage(billCompletionMessage, "");
        billCompletionMessage.className = "message";
    }

    try {
        selectedBill = await apiRequest(
            `/api/v1/bills/${encodeURIComponent(billId)}`
        );

        billDetailsSection.hidden = false;
        renderBillDetails();

        if (scroll) {
            billDetailsSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

function renderBillDetails() {
    if (!selectedBill) {
        billDetailsSection.hidden = true;
        return;
    }

    billDetailsTitle.textContent =
        `Invoice ${selectedBill.invoice_number}`;

    const descriptionParts = [
        selectedBill.customer_name,
        selectedBill.customer_phone,
        selectedBill.status,
        selectedBill.payment_status
    ];
    if (selectedBill.payment_method) {
        descriptionParts.push(paymentMethodLabel(selectedBill.payment_method));
    }
    billDetailsDescription.textContent = descriptionParts.join(" · ");

    printInvoiceButton.hidden = selectedBill.status !== "completed";

    const canModify = permissions.includes("bill:create") &&
        selectedBill.status === "draft";
    const canComplete = permissions.includes("bill:complete") &&
        selectedBill.status === "draft";
    const canReturn = permissions.includes("bill:create") &&
        selectedBill.status === "completed";

    addBillItemSection.hidden = !canModify;
    billCompletionActions.hidden = !canComplete;
    billApprovalMessage.hidden = selectedBill.status !== "draft" || canComplete;
    itemActionsHeading.hidden = !canModify;
    batchReturnActionsHeading.hidden = !canReturn;

    if (canComplete && document.activeElement !== amountReceivedInput) {
        amountReceivedInput.value =
            Number(selectedBill.total_amount || 0).toFixed(2);
    }

    billItemRows.replaceChildren();

    if (!selectedBill.items.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = canModify ? 5 : 4;
        cell.textContent = "No medicines on this bill yet.";
        row.appendChild(cell);
        billItemRows.appendChild(row);
    } else {
        for (const item of selectedBill.items) {
            const row = document.createElement("tr");
            addCell(row, item.medicine_name);
            addCell(row, item.quantity);
            addCell(row, formatMoney(item.unit_price));
            addCell(row, formatMoney(item.total_price));

            if (canModify) {
                const actionsCell = document.createElement("td");
                const actions = document.createElement("div");
                actions.className = "row-actions";

                actions.appendChild(makeButton(
                    "Change quantity",
                    "button button-secondary button-small",
                    () => changeItemQuantity(item, actionsCell)
                ));
                actions.appendChild(makeButton(
                    "Remove",
                    "button button-secondary button-small",
                    () => removeBillItem(item, actionsCell)
                ));

                actionsCell.appendChild(actions);
                row.appendChild(actionsCell);
            }

            billItemRows.appendChild(row);
        }
    }

    billSubtotal.textContent = formatMoney(selectedBill.subtotal);
    billTax.textContent =
        `${formatMoney(selectedBill.tax_amount)} (${selectedBill.tax_percentage}%)`;
    billTotal.textContent = formatMoney(selectedBill.total_amount);

    renderPaymentSummary();
    renderBatchAllocations(selectedBill.batch_allocations || []);
    completeBillButton.disabled = selectedBill.items.length === 0;
}

function renderBatchAllocations(allocations) {
    batchAllocationRows.replaceChildren();
    batchAllocationsSection.hidden = allocations.length === 0;

    const canReturn = permissions.includes("bill:create") &&
        selectedBill?.status === "completed";

    for (const allocation of allocations) {
        const row = document.createElement("tr");
        const medicine = medicines.find(
            (item) => item.id === allocation.medicine_id
        );
        const sold = Number(allocation.quantity_sold) || 0;
        const returned = Number(allocation.quantity_returned) || 0;
        const available = Math.max(sold - returned, 0);

        addCell(row, medicine ? medicine.name : "Unknown medicine");
        addCell(row, allocation.batch_number);
        addCell(row, sold);
        addCell(row, returned);
        addCell(row, available);
        addCell(row, allocation.expiry_date
            ? new Date(allocation.expiry_date).toLocaleDateString()
            : "—");

        if (canReturn) {
            const actionsCell = document.createElement("td");

            if (available > 0) {
                const form = document.createElement("form");
                form.className = "batch-return-form";

                const returnQuantityInput = document.createElement("input");
                returnQuantityInput.type = "number";
                returnQuantityInput.min = "1";
                returnQuantityInput.max = String(available);
                returnQuantityInput.value = "1";
                returnQuantityInput.required = true;
                returnQuantityInput.setAttribute("aria-label", "Return quantity");
                returnQuantityInput.title = `Up to ${available} unit(s) can be returned`;

                const reasonInput = document.createElement("input");
                reasonInput.type = "text";
                reasonInput.minLength = 3;
                reasonInput.maxLength = 250;
                reasonInput.required = true;
                reasonInput.placeholder = "Return reason";
                reasonInput.setAttribute("aria-label", "Return reason");

                const submitButton = document.createElement("button");
                submitButton.type = "submit";
                submitButton.className = "button button-secondary button-small";
                submitButton.textContent = "Return units";

                form.append(returnQuantityInput, reasonInput, submitButton);
                form.addEventListener("submit", async (event) => {
                    event.preventDefault();
                    await returnBatchStock(
                        allocation,
                        Number(returnQuantityInput.value),
                        reasonInput.value,
                        submitButton
                    );
                });
                actionsCell.appendChild(form);
            } else {
                actionsCell.textContent = "Fully returned";
            }

            row.appendChild(actionsCell);
        }

        batchAllocationRows.appendChild(row);
    }
}

async function returnBatchStock(allocation, quantity, reason, submitButton) {
    const available = Math.max(
        (Number(allocation.quantity_sold) || 0) -
        (Number(allocation.quantity_returned) || 0),
        0
    );
    const trimmedReason = reason.trim();

    if (!Number.isInteger(quantity) || quantity <= 0 || quantity > available) {
        showMessage(errorMessage, `Enter a whole number from 1 to ${available}.`);
        return;
    }

    if (trimmedReason.length < 3) {
        showMessage(errorMessage, "The return reason must be at least 3 characters.");
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    submitButton.disabled = true;
    submitButton.textContent = "Recording return…";

    try {
        const result = await apiRequest(
            `/api/v1/bills/${encodeURIComponent(selectedBill.id)}/returns`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    batch_id: allocation.batch_id,
                    quantity,
                    reason: trimmedReason
                })
            }
        );

        showMessage(
            successMessage,
            `${result.quantity_returned} unit(s) returned to batch ${result.batch_number}. ` +
            `Medicine stock is now ${result.medicine_stock}.`
        );
        await loadBills();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Return units";
    }
}

function changeItemQuantity(item, actionsCell) {
    const editor = document.createElement("form");
    editor.className = "item-quantity-editor";

    const input = document.createElement("input");
    input.type = "number";
    input.min = "1";
    input.step = "1";
    input.required = true;
    input.value = String(item.quantity);
    input.setAttribute("aria-label", `New quantity for ${item.medicine_name}`);

    const saveButton = document.createElement("button");
    saveButton.type = "submit";
    saveButton.className = "button button-primary button-small";
    saveButton.textContent = "Save";

    const cancelButton = makeButton(
        "Cancel",
        "button button-secondary button-small",
        () => renderBillDetails()
    );

    editor.append(input, saveButton, cancelButton);
    actionsCell.replaceChildren(editor);
    input.focus();
    input.select();

    editor.addEventListener("submit", async (event) => {
        event.preventDefault();
        const quantity = Number(input.value);
        if (!Number.isInteger(quantity) || quantity <= 0) {
            showMessage(errorMessage, "Enter a whole number greater than zero.");
            input.focus();
            return;
        }

        saveButton.disabled = true;
        showMessage(errorMessage, "");
        try {
            await apiRequest(
                `/api/v1/bills/items/${encodeURIComponent(item.id)}`,
                {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ quantity })
                }
            );

            showMessage(successMessage, "Bill item quantity updated.");
            await openBill(selectedBill.id, false);
            await loadBills();
        } catch (error) {
            showMessage(errorMessage, error.message);
            saveButton.disabled = false;
        }
    });
}

async function removeBillItem(item, button) {
    const confirmed = await window.showConfirmDialog({
        title: "Remove medicine from draft?",
        message: `Remove ${item.medicine_name} from this draft bill?`,
        confirmText: "Remove item"
    });
    if (!confirmed) {
        return;
    }

    showMessage(errorMessage, "");
    button.disabled = true;

    try {
        await apiRequest(
            `/api/v1/bills/items/${encodeURIComponent(item.id)}`,
            { method: "DELETE" }
        );

        showMessage(successMessage, "Medicine removed from the draft bill.");
        await openBill(selectedBill.id, false);
        await loadBills();
    } catch (error) {
        showMessage(errorMessage, error.message);
        button.disabled = false;
    }
}

createBillForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    createBillButton.disabled = true;

    try {
        const bill = await apiRequest("/api/v1/bills", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                customer_name: customerNameInput.value.trim(),
                customer_phone: customerPhoneInput.value.trim()
            })
        });

        createBillForm.reset();
        showMessage(successMessage, `Draft ${bill.invoice_number} created.`);
        await loadBills();
        await openBill(bill.id);
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        createBillButton.disabled = false;
    }
});

medicineSelect.addEventListener("change", () => {
    const medicine = medicines.find(
        (item) => item.id === medicineSelect.value
    );
    if (medicine) {
        quantityInput.max = String(medicine.stock);
    }
});

medicineSearchInput.addEventListener("input", () => {
    scheduleMedicineSearch(medicineSearchInput.value);
});

addBillItemForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedBill || selectedBill.status !== "draft") {
        return;
    }

    const medicine = medicines.find(
        (item) => item.id === medicineSelect.value
    );
    const quantity = Number(quantityInput.value);

    if (!medicine) {
        showMessage(errorMessage, "Choose a medicine.");
        return;
    }

    const alreadyOnBill = selectedBill.items
        .filter((item) => item.medicine_id === medicine.id)
        .reduce((total, item) => total + item.quantity, 0);
    const remainingStock = medicine.stock - alreadyOnBill;

    if (!Number.isInteger(quantity) || quantity <= 0) {
        showMessage(errorMessage, "Enter a whole number greater than zero.");
        return;
    }

    if (quantity > remainingStock) {
        showMessage(
            errorMessage,
            `Only ${Math.max(remainingStock, 0)} more unit(s) of ${medicine.name} can be added based on current stock.`
        );
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    addItemButton.disabled = true;

    try {
        await apiRequest("/api/v1/bills/items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                bill_id: selectedBill.id,
                medicine_id: medicine.id,
                quantity
            })
        });

        addBillItemForm.reset();
        quantityInput.removeAttribute("max");
        scheduleMedicineSearch("");
        showMessage(successMessage, `${medicine.name} added to the draft bill.`);
        await openBill(selectedBill.id, false);
        await loadBills();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        addItemButton.disabled = false;
    }
});

completeBillButton.addEventListener("click", async () => {
    if (!selectedBill || selectedBill.status !== "draft") {
        return;
    }

    const paymentMethod = paymentMethodInput.value;
    const amountReceived = Number(amountReceivedInput.value);
    const totalAmount = Number(selectedBill.total_amount) || 0;
    const receivedCents = Math.round(amountReceived * 100);
    const totalCents = Math.round(totalAmount * 100);

    if (!["cash", "card", "upi"].includes(paymentMethod)) {
        showMessage(errorMessage, "Choose Cash, Card, or UPI as the payment method.");
        paymentMethodInput.focus();
        return;
    }

    if (!Number.isFinite(amountReceived) || receivedCents <= 0) {
        showMessage(errorMessage, "Enter a valid amount received.");
        amountReceivedInput.focus();
        return;
    }

    if (receivedCents < totalCents) {
        showMessage(
            errorMessage,
            `Amount received must be at least ${formatMoney(totalAmount)}.`
        );
        amountReceivedInput.focus();
        return;
    }

    if (paymentMethod !== "cash" && receivedCents !== totalCents) {
        showMessage(
            errorMessage,
            `${paymentMethodLabel(paymentMethod)} payment must equal the bill total of ${formatMoney(totalAmount)}.`
        );
        amountReceivedInput.focus();
        return;
    }

    const changeDue = Math.max(0, receivedCents - totalCents) / 100;
    const paymentDescription = paymentMethod === "cash" && changeDue > 0
        ? `${paymentMethodLabel(paymentMethod)} · received ${formatMoney(amountReceived)} · change due ${formatMoney(changeDue)}`
        : `${paymentMethodLabel(paymentMethod)} · received ${formatMoney(amountReceived)}`;

    completeBillButton.disabled = true;
    const confirmed = await window.showConfirmDialog({
        title: "Complete bill?",
        message: `Complete invoice ${selectedBill.invoice_number}? ${paymentDescription}. Stock will be deducted.`,
        confirmText: "Complete bill",
        variant: "simple"
    });

    if (!confirmed) {
        completeBillButton.disabled = false;
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    showMessage(billCompletionMessage, "");
    billCompletionMessage.className = "message";

    try {
        await apiRequest(
            `/api/v1/bills/${encodeURIComponent(selectedBill.id)}/complete`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    payment_method: paymentMethod,
                    amount_received: amountReceived
                })
            }
        );

        const completionText =
            `Sale completed using ${paymentMethodLabel(paymentMethod)}. ` +
            `Stock was deducted and the batch allocation was recorded.`;
        billCompletionMessage.className = "message message-success";
        showMessage(billCompletionMessage, completionText);
        showMessage(successMessage, completionText);
        await loadBills();
    } catch (error) {
        showMessage(errorMessage, error.message);
        billCompletionMessage.className = "message message-error";
        showMessage(billCompletionMessage, error.message);
    } finally {
        completeBillButton.disabled = false;
    }
});

refreshButton.addEventListener("click", loadBills);

closeDetailsButton.addEventListener("click", () => {
    selectedBill = null;
    billDetailsSection.hidden = true;
});

printInvoiceButton.addEventListener("click", () => {
    if (selectedBill?.status !== "completed") {
        return;
    }
    window.print();
});

async function initializePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await requestCurrentUser();
        permissions = currentUser.permissions || [];

        if (!permissions.includes("bill:read")) {
            showMessage(errorMessage, "Your account does not have permission to view bills.");
            statusMessage.hidden = true;
            return;
        }

        if (permissions.includes("bill:create")) {
            createBillSection.hidden = false;
            const initialSearchId = ++medicineSearchRequestId;
            await searchMedicines("", initialSearchId);
        }

        await loadBills();
    } catch (error) {
        showMessage(errorMessage, error.message);
        statusMessage.hidden = true;

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();
