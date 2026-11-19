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

// Schedule H & Prescription DOM Elements
const scheduleHAlert = document.getElementById("scheduleHAlert");
const scheduleHAlertText = document.getElementById("scheduleHAlertText");
const prescriptionSection = document.getElementById("prescriptionSection");
const prescriptionStatusBadge = document.getElementById("prescriptionStatusBadge");
const prescriptionActiveCard = document.getElementById("prescriptionActiveCard");
const rxFileName = document.getElementById("rxFileName");
const rxDoctorName = document.getElementById("rxDoctorName");
const rxDoctorReg = document.getElementById("rxDoctorReg");
const rxUploadMeta = document.getElementById("rxUploadMeta");
const viewPrescriptionBtn = document.getElementById("viewPrescriptionBtn");
const removePrescriptionBtn = document.getElementById("removePrescriptionBtn");
const prescriptionUploadForm = document.getElementById("prescriptionUploadForm");
const rxDropzone = document.getElementById("rxDropzone");
const prescriptionFileInput = document.getElementById("prescriptionFileInput");
const selectedFilePreview = document.getElementById("selectedFilePreview");
const doctorNameInput = document.getElementById("doctorNameInput");
const doctorRegNoInput = document.getElementById("doctorRegNoInput");
const docNameStar = document.getElementById("docNameStar");
const docRegStar = document.getElementById("docRegStar");
const uploadPrescriptionButton = document.getElementById("uploadPrescriptionButton");
const prescriptionActionStatus = document.getElementById("prescriptionActionStatus");
const completeBillRxWarning = document.getElementById("completeBillRxWarning");

// Digital Receipts & Messaging DOM Elements
const customerEmailInput = document.getElementById("customerEmail");
const emailReceiptButton = document.getElementById("emailReceiptButton");
const whatsappReceiptButton = document.getElementById("whatsappReceiptButton");
const receiptStatusBanner = document.getElementById("receiptStatusBanner");
const receiptStatusText = document.getElementById("receiptStatusText");
const completeCustomerEmail = document.getElementById("completeCustomerEmail");
const sendReceiptCheckbox = document.getElementById("sendReceiptCheckbox");

// Barcode & Camera Scanner DOM Elements
const openCameraScannerButton = document.getElementById("openCameraScannerButton");
const barcodeInput = document.getElementById("barcodeInput");
const barcodeLookupBtn = document.getElementById("barcodeLookupBtn");
const autoAddScanCheckbox = document.getElementById("autoAddScanCheckbox");
const barcodeScanFeedback = document.getElementById("barcodeScanFeedback");
const scannerModal = document.getElementById("scannerModal");
const scannerModalBackdrop = document.getElementById("scannerModalBackdrop");
const closeScannerModalBtn = document.getElementById("closeScannerModalBtn");
const scannerVideo = document.getElementById("scannerVideo");
const scannerStatusBadge = document.getElementById("scannerStatusBadge");
const switchCameraBtn = document.getElementById("switchCameraBtn");
const toggleTorchBtn = document.getElementById("toggleTorchBtn");

let activeScannerStream = null;
let scannerAnimFrameId = null;
let currentFacingMode = "environment";
let lastScannedCode = null;
let lastScanTimestamp = 0;
let isTorchOn = false;

// Prescription Lightbox Modal Elements
const prescriptionModal = document.getElementById("prescriptionModal");
const rxModalBackdrop = document.getElementById("rxModalBackdrop");
const rxModalTitle = document.getElementById("rxModalTitle");
const rxModalSubtitle = document.getElementById("rxModalSubtitle");
const closeRxModalBtn = document.getElementById("closeRxModalBtn");
const rxImageContainer = document.getElementById("rxImageContainer");
const rxModalImage = document.getElementById("rxModalImage");
const rxPdfContainer = document.getElementById("rxPdfContainer");
const rxPdfLink = document.getElementById("rxPdfLink");

// Redesigned Printable Invoice DOM Elements
const printableInvoiceCard = document.getElementById("printableInvoiceCard");
const invStoreName = document.getElementById("invStoreName");
const invStoreAddress = document.getElementById("invStoreAddress");
const invStorePhone = document.getElementById("invStorePhone");
const invStoreLicense = document.getElementById("invStoreLicense");
const invNumberBadge = document.getElementById("invNumberBadge");
const invCustomerName = document.getElementById("invCustomerName");
const invCustomerPhone = document.getElementById("invCustomerPhone");
const invCustomerEmail = document.getElementById("invCustomerEmail");
const invDateStr = document.getElementById("invDateStr");
const invPaymentMethod = document.getElementById("invPaymentMethod");
const invRxInfoBox = document.getElementById("invRxInfoBox");
const invRxDoctor = document.getElementById("invRxDoctor");
const invRxReg = document.getElementById("invRxReg");
const invTableBody = document.getElementById("invTableBody");
const invSubtotal = document.getElementById("invSubtotal");
const invTaxLabel = document.getElementById("invTaxLabel");
const invTaxAmount = document.getElementById("invTaxAmount");
const invGrandTotal = document.getElementById("invGrandTotal");
const invPaidViaLabel = document.getElementById("invPaidViaLabel");
const invAmountReceived = document.getElementById("invAmountReceived");
const invChangeRow = document.getElementById("invChangeRow");
const invChangeDue = document.getElementById("invChangeDue");
const invActionColHeader = document.getElementById("invActionColHeader");

// POS Navigation Tabs & View Elements
const tabPosBtn = document.getElementById("tabPosBtn");
const tabHistoryBtn = document.getElementById("tabHistoryBtn");
const tabBillCount = document.getElementById("tabBillCount");
const quickNewSaleBtn = document.getElementById("quickNewSaleBtn");
const posWorkstationView = document.getElementById("posWorkstationView");
const billHistoryView = document.getElementById("billHistoryView");
const quickCashChips = document.getElementById("quickCashChips");

let storeSettings = {};
let selectedPrescriptionFile = null;

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
if (billTotal && billTotal.closest(".bill-totals")) {
    billTotal.closest(".bill-totals").insertAdjacentElement("afterend", paymentSummary);
}

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
        cell.colSpan = 8;
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

        const rxCell = document.createElement("td");
        if (bill.has_prescription) {
            rxCell.innerHTML = `<span class="rx-badge rx-attached" style="font-size:0.75rem;">✓ Attached</span>`;
        } else if (bill.requires_prescription) {
            rxCell.innerHTML = `<span class="rx-badge rx-required" style="font-size:0.75rem;">⚠️ Required</span>`;
        } else {
            rxCell.innerHTML = `<span style="color:var(--ms-muted); font-size:0.8rem;">—</span>`;
        }
        row.appendChild(rxCell);

        const receiptCell = document.createElement("td");
        if (bill.receipt_email_sent) {
            receiptCell.innerHTML = `<span class="receipt-pill receipt-pill-sent" title="Digital email receipt sent">✉️ Sent</span>`;
        } else if (bill.status === "completed") {
            receiptCell.innerHTML = `<span class="receipt-pill receipt-pill-none" title="Receipt not yet emailed">Unsent</span>`;
        } else {
            receiptCell.innerHTML = `<span style="color:var(--ms-muted); font-size:0.8rem;">—</span>`;
        }
        row.appendChild(receiptCell);

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

async function loadBills(refreshSelected = false) {
    statusMessage.textContent = "Loading bills…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        bills = await apiRequest("/api/v1/bills");
        renderBills();

        billListDescription.textContent =
            `${bills.length} bill${bills.length === 1 ? "" : "s"}`;
        if (tabBillCount) tabBillCount.textContent = String(bills.length);
        statusMessage.textContent = bills.length ? "" : "No bills found.";
        statusMessage.hidden = bills.length > 0;

        if (selectedBill) {
            const stillExists = bills.some((bill) => bill.id === selectedBill.id);
            if (stillExists) {
                if (refreshSelected) {
                    await openBill(selectedBill.id, false);
                }
            } else {
                selectedBill = null;
                billDetailsSection.hidden = true;
                if (permissions.includes("bill:create")) {
                    createBillSection.hidden = false;
                }
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

        switchTab("pos");
        createBillSection.hidden = true;
        billDetailsSection.hidden = false;
        renderBillDetails();

        if (selectedBill.status === "draft") {
            window.setTimeout(() => {
                if (barcodeInput && !addBillItemSection.hidden) {
                    barcodeInput.focus();
                    barcodeInput.select();
                }
            }, 150);
        }

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
        selectedBill.customer_phone
    ];
    if (selectedBill.customer_email) {
        descriptionParts.push(selectedBill.customer_email);
    }
    descriptionParts.push(selectedBill.status);
    descriptionParts.push(selectedBill.payment_status);
    if (selectedBill.payment_method) {
        descriptionParts.push(paymentMethodLabel(selectedBill.payment_method));
    }
    billDetailsDescription.textContent = descriptionParts.join(" · ");

    const isCompleted = selectedBill.status === "completed";
    printInvoiceButton.hidden = !isCompleted;
    if (emailReceiptButton) emailReceiptButton.hidden = !isCompleted;
    if (whatsappReceiptButton) whatsappReceiptButton.hidden = !isCompleted;

    if (receiptStatusBanner) {
        if (isCompleted && selectedBill.receipt_email_sent) {
            receiptStatusBanner.hidden = false;
            const sentAtText = selectedBill.receipt_email_sent_at
                ? ` on ${new Date(selectedBill.receipt_email_sent_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}`
                : "";
            receiptStatusText.textContent = `Invoice receipt emailed to ${selectedBill.customer_email || "customer"}${sentAtText}.`;
        } else {
            receiptStatusBanner.hidden = true;
        }
    }

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

    if (canComplete) {
        if (document.activeElement !== amountReceivedInput) {
            amountReceivedInput.value =
                Number(selectedBill.total_amount || 0).toFixed(2);
        }
        if (completeCustomerEmail && document.activeElement !== completeCustomerEmail) {
            completeCustomerEmail.value = selectedBill.customer_email || "";
        }
        if (sendReceiptCheckbox) {
            sendReceiptCheckbox.checked = Boolean(selectedBill.customer_email);
        }
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

            const nameCell = document.createElement("td");
            nameCell.textContent = item.medicine_name;
            if (item.is_controlled_substance) {
                const rxBadge = document.createElement("span");
                rxBadge.className = "badge-rx-controlled";
                rxBadge.textContent = "Schedule H";
                rxBadge.title = "Schedule H / Controlled Substance: Prescription Required";
                nameCell.appendChild(rxBadge);
            }
            row.appendChild(nameCell);

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
    renderPrescriptionDetails(canModify);
    renderPrintableInvoice();
}

function renderPrintableInvoice() {
    if (!printableInvoiceCard || !selectedBill) return;

    printableInvoiceCard.hidden = false;

    const isCompleted = selectedBill.status === "completed";

    // 1. Store Header Info
    if (invStoreName) invStoreName.textContent = storeSettings.store_name || "MediStock Pharmacy";
    if (invStoreAddress) invStoreAddress.textContent = storeSettings.store_address || "Tirupati, Andhra Pradesh, 517505";
    if (invStorePhone) invStorePhone.textContent = storeSettings.store_phone || "+91 78945 61230";
    if (invStoreLicense) invStoreLicense.textContent = storeSettings.store_license_number || "DL-123456789";

    const invMemoTitle = document.getElementById("invMemoTitle");
    const invMemoSub = document.getElementById("invMemoSub");
    if (invMemoTitle) invMemoTitle.textContent = isCompleted ? "TAX INVOICE" : "DRAFT INVOICE";
    if (invMemoSub) invMemoSub.textContent = isCompleted ? "CASH / CREDIT MEMO" : "ACTIVE SALE IN PROGRESS";

    if (invNumberBadge) {
        invNumberBadge.textContent = selectedBill.invoice_number || "INV-000000";
        invNumberBadge.className = isCompleted ? "inv-number-badge inv-number-paid" : "inv-number-badge inv-number-draft";
    }

    // 2. Customer & Invoice Meta
    if (invCustomerName) invCustomerName.innerHTML = `<strong>${selectedBill.customer_name || "Customer"}</strong>`;
    if (invCustomerPhone) invCustomerPhone.textContent = `Ph: ${selectedBill.customer_phone || "—"}`;
    if (invCustomerEmail) {
        if (selectedBill.customer_email) {
            invCustomerEmail.hidden = false;
            invCustomerEmail.textContent = `Email: ${selectedBill.customer_email}`;
        } else {
            invCustomerEmail.hidden = true;
        }
    }

    const billDate = selectedBill.completed_at ? new Date(selectedBill.completed_at) : new Date();
    if (invDateStr) {
        invDateStr.textContent = billDate.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    if (invPaymentMethod) {
        invPaymentMethod.textContent = isCompleted
            ? `${(selectedBill.payment_method || "CASH").toUpperCase()} (PAID)`
            : "PAYMENT PENDING";
    }

    // Prescription info
    if (invRxInfoBox) {
        if (selectedBill.prescription) {
            invRxInfoBox.hidden = false;
            if (invRxDoctor) invRxDoctor.textContent = `Dr. ${selectedBill.prescription.doctor_name || "Physician"}`;
            if (invRxReg) invRxReg.textContent = selectedBill.prescription.doctor_reg_no || "Registered";
        } else {
            invRxInfoBox.hidden = true;
        }
    }

    // 3. Table Rows with Batch allocations
    const canModify = permissions.includes("bill:create") && selectedBill.status === "draft";
    if (invActionColHeader) {
        invActionColHeader.hidden = !canModify;
    }

    if (invTableBody) {
        invTableBody.replaceChildren();

        const batchMap = {};
        (selectedBill.batch_allocations || []).forEach((b) => {
            batchMap[b.medicine_id] = b;
        });

        if (!selectedBill.items || selectedBill.items.length === 0) {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td colspan="${canModify ? 8 : 7}" style="text-align:center; color:var(--ms-slate); padding:20px;">
                📦 No medicines added yet. Scan a barcode above or search to ring up items.
            </td>`;
            invTableBody.appendChild(tr);
        } else {
            selectedBill.items.forEach((item, index) => {
                const tr = document.createElement("tr");

                const batchInfo = batchMap[item.medicine_id];
                const batchNum = batchInfo ? batchInfo.batch_number : `B-${item.medicine_id.slice(-4).toUpperCase()}`;
                const expiryStr = batchInfo && batchInfo.expiry_date
                    ? new Date(batchInfo.expiry_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" })
                    : "—";

                const numTd = document.createElement("td");
                numTd.style.color = "var(--ms-slate)";
                numTd.textContent = String(index + 1);
                tr.appendChild(numTd);

                const nameTd = document.createElement("td");
                nameTd.innerHTML = `<strong>${item.medicine_name}</strong>${item.is_controlled_substance ? ' <span class="badge-rx-controlled" style="margin-left:6px; font-size:0.68rem;">Schedule H</span>' : ''}`;
                tr.appendChild(nameTd);

                const batchTd = document.createElement("td");
                batchTd.innerHTML = `<code>${batchNum}</code>`;
                tr.appendChild(batchTd);

                const expTd = document.createElement("td");
                expTd.textContent = expiryStr;
                tr.appendChild(expTd);

                const qtyTd = document.createElement("td");
                qtyTd.style.textAlign = "center";

                if (canModify) {
                    const stepper = document.createElement("div");
                    stepper.className = "inv-qty-stepper";

                    const decBtn = document.createElement("button");
                    decBtn.type = "button";
                    decBtn.className = "inv-stepper-btn";
                    decBtn.textContent = "−";
                    decBtn.title = "Decrease quantity";
                    decBtn.addEventListener("click", async () => {
                        if (item.quantity > 1) {
                            try {
                                await apiRequest(`/api/v1/bills/items/${encodeURIComponent(item.id)}`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ quantity: item.quantity - 1 })
                                });
                                await openBill(selectedBill.id, false);
                                await loadBills();
                            } catch (err) {
                                showMessage(errorMessage, err.message);
                            }
                        } else {
                            await removeBillItem(item, decBtn);
                        }
                    });

                    const qtyVal = document.createElement("span");
                    qtyVal.className = "inv-qty-val";
                    qtyVal.textContent = String(item.quantity);
                    qtyVal.title = "Click to edit quantity";
                    qtyVal.addEventListener("click", () => changeItemQuantity(item, qtyTd));

                    const incBtn = document.createElement("button");
                    incBtn.type = "button";
                    incBtn.className = "inv-stepper-btn";
                    incBtn.textContent = "+";
                    incBtn.title = "Increase quantity";
                    incBtn.addEventListener("click", async () => {
                        try {
                            await apiRequest(`/api/v1/bills/items/${encodeURIComponent(item.id)}`, {
                                method: "PATCH",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ quantity: item.quantity + 1 })
                            });
                            await openBill(selectedBill.id, false);
                            await loadBills();
                        } catch (err) {
                            showMessage(errorMessage, err.message);
                        }
                    });

                    stepper.append(decBtn, qtyVal, incBtn);
                    qtyTd.appendChild(stepper);
                } else {
                    qtyTd.style.fontWeight = "600";
                    qtyTd.textContent = String(item.quantity);
                }
                tr.appendChild(qtyTd);

                const unitPriceTd = document.createElement("td");
                unitPriceTd.style.textAlign = "right";
                unitPriceTd.textContent = formatMoney(item.unit_price);
                tr.appendChild(unitPriceTd);

                const totalTd = document.createElement("td");
                totalTd.style.textAlign = "right";
                totalTd.style.fontWeight = "700";
                totalTd.style.color = "var(--ms-primary)";
                totalTd.textContent = formatMoney(item.total_price);
                tr.appendChild(totalTd);

                if (canModify) {
                    const actionTd = document.createElement("td");
                    actionTd.className = "inv-action-col";
                    actionTd.style.textAlign = "center";
                    const removeBtn = document.createElement("button");
                    removeBtn.type = "button";
                    removeBtn.className = "inv-btn-remove";
                    removeBtn.innerHTML = "🗑️";
                    removeBtn.title = `Remove ${item.medicine_name}`;
                    removeBtn.addEventListener("click", () => removeBillItem(item, removeBtn));
                    actionTd.appendChild(removeBtn);
                    tr.appendChild(actionTd);
                }

                invTableBody.appendChild(tr);
            });
        }
    }

    // 4. Totals & Payment Summary
    if (invSubtotal) invSubtotal.textContent = formatMoney(selectedBill.subtotal);
    if (invTaxLabel) invTaxLabel.textContent = `GST Tax (${selectedBill.tax_percentage || 0}%):`;
    if (invTaxAmount) invTaxAmount.textContent = formatMoney(selectedBill.tax_amount);
    if (invGrandTotal) invGrandTotal.textContent = formatMoney(selectedBill.total_amount);

    if (isCompleted) {
        if (invPaidViaLabel) invPaidViaLabel.textContent = `Paid via ${paymentMethodLabel(selectedBill.payment_method)}:`;
        if (invAmountReceived) invAmountReceived.textContent = formatMoney(selectedBill.amount_received || selectedBill.total_amount);

        if (invChangeRow && invChangeDue) {
            const change = Number(selectedBill.change_due || 0);
            if (change > 0) {
                invChangeRow.hidden = false;
                invChangeDue.textContent = formatMoney(change);
            } else {
                invChangeRow.hidden = true;
            }
        }
    } else {
        if (invPaidViaLabel) invPaidViaLabel.textContent = "Status:";
        if (invAmountReceived) invAmountReceived.textContent = "Draft Sale (Pending)";
        if (invChangeRow) invChangeRow.hidden = true;
    }
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
                customer_phone: customerPhoneInput.value.trim(),
                customer_email: customerEmailInput ? customerEmailInput.value.trim() || null : null
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
        const customerEmailVal = completeCustomerEmail ? completeCustomerEmail.value.trim() : "";
        const shouldSendReceipt = sendReceiptCheckbox ? sendReceiptCheckbox.checked : false;

        const updated = await apiRequest(
            `/api/v1/bills/${encodeURIComponent(selectedBill.id)}/complete`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    payment_method: paymentMethod,
                    amount_received: amountReceived,
                    customer_email: customerEmailVal || null,
                    send_email_receipt: shouldSendReceipt && Boolean(customerEmailVal)
                })
            }
        );

        let completionText =
            `Sale completed using ${paymentMethodLabel(paymentMethod)}. ` +
            `Stock was deducted and the batch allocation was recorded.`;
        if (shouldSendReceipt && customerEmailVal) {
            completionText += ` Digital invoice receipt is being emailed to ${customerEmailVal}.`;
        }

        billCompletionMessage.className = "message message-success";
        showMessage(billCompletionMessage, completionText);
        showMessage(successMessage, completionText);
        await loadBills();
        await openBill(selectedBill.id, false);
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
    if (permissions.includes("bill:create")) {
        createBillSection.hidden = false;
    }
});

if (quickNewSaleBtn) {
    quickNewSaleBtn.addEventListener("click", () => {
        selectedBill = null;
        switchTab("pos");
        billDetailsSection.hidden = true;
        if (createBillSection) {
            createBillSection.hidden = false;
            if (customerNameInput) customerNameInput.focus();
        }
    });
}

function switchTab(viewName) {
    if (viewName === "history") {
        if (tabPosBtn) {
            tabPosBtn.classList.remove("is-active");
            tabPosBtn.setAttribute("aria-selected", "false");
        }
        if (tabHistoryBtn) {
            tabHistoryBtn.classList.add("is-active");
            tabHistoryBtn.setAttribute("aria-selected", "true");
        }
        if (posWorkstationView) posWorkstationView.hidden = true;
        if (billHistoryView) billHistoryView.hidden = false;
    } else {
        if (tabHistoryBtn) {
            tabHistoryBtn.classList.remove("is-active");
            tabHistoryBtn.setAttribute("aria-selected", "false");
        }
        if (tabPosBtn) {
            tabPosBtn.classList.add("is-active");
            tabPosBtn.setAttribute("aria-selected", "true");
        }
        if (billHistoryView) billHistoryView.hidden = true;
        if (posWorkstationView) posWorkstationView.hidden = false;
    }
}

if (tabPosBtn) tabPosBtn.addEventListener("click", () => switchTab("pos"));
if (tabHistoryBtn) tabHistoryBtn.addEventListener("click", () => switchTab("history"));

function updateLiveChangeCalculation() {
    if (!selectedBill || selectedBill.status === "completed") return;

    const total = Number(selectedBill.total_amount || 0);
    const received = Number(amountReceivedInput.value || 0);

    if (received >= total && total > 0) {
        const change = received - total;
        if (invChangeRow) invChangeRow.hidden = false;
        if (invChangeDue) invChangeDue.textContent = formatMoney(change);
        if (invAmountReceived) invAmountReceived.textContent = formatMoney(received);
        if (invPaidViaLabel) invPaidViaLabel.textContent = `Tendered (${(paymentMethodInput ? paymentMethodInput.value : "cash").toUpperCase()}):`;
    } else {
        if (invChangeRow) invChangeRow.hidden = true;
        if (invAmountReceived) invAmountReceived.textContent = "Draft Sale (Pending)";
        if (invPaidViaLabel) invPaidViaLabel.textContent = "Status:";
    }
}

if (quickCashChips) {
    quickCashChips.addEventListener("click", (e) => {
        const btn = e.target.closest(".cash-chip");
        if (!btn || !selectedBill) return;

        const tender = btn.dataset.tender;
        const total = Number(selectedBill.total_amount || 0);

        if (tender === "exact") {
            amountReceivedInput.value = total.toFixed(2);
        } else {
            const addVal = Number(tender) || 0;
            const rounded = Math.ceil(total / addVal) * addVal;
            amountReceivedInput.value = (rounded > total ? rounded : total + addVal).toFixed(2);
        }

        quickCashChips.querySelectorAll(".cash-chip").forEach((c) => c.classList.remove("is-active"));
        btn.classList.add("is-active");
        updateLiveChangeCalculation();
    });
}

if (amountReceivedInput) {
    amountReceivedInput.addEventListener("input", updateLiveChangeCalculation);
}

if (paymentMethodInput) {
    paymentMethodInput.addEventListener("change", () => {
        if (paymentMethodInput.value !== "cash" && selectedBill) {
            amountReceivedInput.value = Number(selectedBill.total_amount || 0).toFixed(2);
            updateLiveChangeCalculation();
        }
    });
}

window.addEventListener("keydown", (e) => {
    // Ctrl+Enter: complete sale
    if (e.ctrlKey && e.key === "Enter") {
        if (selectedBill && selectedBill.status === "draft" && !billCompletionActions.hidden) {
            e.preventDefault();
            completeBillButton.click();
        }
    }
    // F2: focus barcode input
    if (e.key === "F2") {
        e.preventDefault();
        if (barcodeInput && !addBillItemSection.hidden) {
            barcodeInput.focus();
            barcodeInput.select();
        }
    }
});

printInvoiceButton.addEventListener("click", () => {
    if (selectedBill?.status !== "completed") {
        return;
    }
    window.print();
});

// Digital Email Receipt Action
if (emailReceiptButton) {
    emailReceiptButton.addEventListener("click", async () => {
        if (!selectedBill || selectedBill.status !== "completed") return;

        let targetEmail = (selectedBill.customer_email || "").trim();
        if (!targetEmail) {
            targetEmail = window.prompt("Enter customer email address to deliver digital receipt:", "");
            if (!targetEmail || !targetEmail.trim()) return;
            targetEmail = targetEmail.trim();
        }

        emailReceiptButton.disabled = true;
        emailReceiptButton.textContent = "Delivering receipt…";
        showMessage(errorMessage, "");

        try {
            const res = await apiRequest(`/api/v1/bills/${encodeURIComponent(selectedBill.id)}/send-receipt`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: targetEmail })
            });

            selectedBill.customer_email = targetEmail;
            selectedBill.receipt_email_sent = true;
            selectedBill.receipt_email_sent_at = res.sent_at || new Date().toISOString();
            renderBillDetails();
            await loadBills();

            showMessage(successMessage, res.message || `Invoice receipt successfully sent to ${targetEmail}.`);
        } catch (err) {
            showMessage(errorMessage, err.message);
        } finally {
            emailReceiptButton.disabled = false;
            emailReceiptButton.textContent = "📧 Email receipt";
        }
    });
}

// Digital WhatsApp Receipt Action
if (whatsappReceiptButton) {
    whatsappReceiptButton.addEventListener("click", () => {
        if (!selectedBill || selectedBill.status !== "completed") return;

        let phone = (selectedBill.customer_phone || "").replace(/\D/g, "");
        if (!phone) {
            phone = window.prompt("Enter customer WhatsApp mobile number (with country code):", "");
            if (!phone) return;
            phone = phone.replace(/\D/g, "");
        }

        // Default to India country code 91 if standard 10-digit number
        if (phone.length === 10) {
            phone = "91" + phone;
        }

        const inv = selectedBill.invoice_number || "INV";
        const cust = selectedBill.customer_name || "Customer";
        const total = formatMoney(selectedBill.total_amount);
        const sub = formatMoney(selectedBill.subtotal);
        const tax = `${formatMoney(selectedBill.tax_amount)} (${selectedBill.tax_percentage}%)`;
        const method = (selectedBill.payment_method || "Cash").toUpperCase();
        const dateStr = new Date().toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });

        let itemsText = "";
        if (selectedBill.items && selectedBill.items.length) {
            itemsText = selectedBill.items.map((it, idx) =>
                `${idx + 1}. *${it.medicine_name}* x ${it.quantity} = ${formatMoney(it.total_price)}`
            ).join("\n");
        } else {
            itemsText = "Prescription medicines";
        }

        const message =
`*🏥 MEDISTOCK PHARMACY*
*Tax Invoice / Digital Bill Receipt*
━━━━━━━━━━━━━━━━━━━━━
*Invoice:* ${inv}
*Date:* ${dateStr}
*Customer:* ${cust}
━━━━━━━━━━━━━━━━━━━━━
*ITEMS PURCHASED:*
${itemsText}
━━━━━━━━━━━━━━━━━━━━━
*Subtotal:* ${sub}
*GST Tax:* ${tax}
*Grand Total:* *${total}*
*Payment Method:* ${method} (Paid)
━━━━━━━━━━━━━━━━━━━━━
_Thank you for choosing MediStock!_
_Helpline: +91 78945 61230_`;

        const waUrl = `https://api.whatsapp.com/send?phone=${encodeURIComponent(phone)}&text=${encodeURIComponent(message)}`;
        window.open(waUrl, "_blank");
    });
}

// Schedule H & Prescription Management Logic
function renderPrescriptionDetails(canModify) {
    if (!selectedBill) return;

    // 1. Schedule H Banner
    if (selectedBill.requires_prescription) {
        scheduleHAlert.hidden = false;
        const meds = (selectedBill.controlled_medicines || []).join(", ") || "Controlled medicines";
        scheduleHAlertText.textContent = `This bill contains Schedule H / controlled substances (${meds}). A valid doctor's prescription must be attached before completing the sale.`;
    } else {
        scheduleHAlert.hidden = true;
    }

    // 2. Prescription Attached Card vs Upload Form
    if (selectedBill.prescription) {
        const rx = selectedBill.prescription;
        prescriptionActiveCard.hidden = false;
        prescriptionUploadForm.hidden = true;

        prescriptionStatusBadge.className = "rx-badge rx-attached";
        prescriptionStatusBadge.textContent = "✓ Prescription Attached";

        rxFileName.textContent = rx.file_name || "prescription";
        rxDoctorName.textContent = rx.doctor_name || "—";
        rxDoctorReg.textContent = rx.doctor_reg_no || "—";

        const uploadDate = rx.uploaded_at ? new Date(rx.uploaded_at).toLocaleString() : "";
        rxUploadMeta.textContent = uploadDate ? `Attached ${uploadDate}` : "";

        removePrescriptionBtn.hidden = !canModify;
    } else {
        prescriptionActiveCard.hidden = true;

        if (selectedBill.requires_prescription) {
            prescriptionStatusBadge.className = "rx-badge rx-required";
            prescriptionStatusBadge.textContent = "⚠️ Prescription Required";
            docNameStar.hidden = false;
            docRegStar.hidden = false;
        } else {
            prescriptionStatusBadge.className = "rx-badge rx-optional";
            prescriptionStatusBadge.textContent = "Optional Rx";
            docNameStar.hidden = true;
            docRegStar.hidden = true;
        }

        prescriptionUploadForm.hidden = !canModify;
    }

    // 3. Complete Bill Button Enforcement
    const missingRequiredRx = selectedBill.requires_prescription && !selectedBill.prescription;
    if (missingRequiredRx) {
        completeBillButton.disabled = true;
        completeBillRxWarning.hidden = false;
    } else {
        completeBillRxWarning.hidden = true;
        completeBillButton.disabled = selectedBill.items.length === 0;
    }
}

// Prescription File Input Handling
function handleSelectedPrescriptionFile(file) {
    if (!file) {
        selectedPrescriptionFile = null;
        selectedFilePreview.hidden = true;
        uploadPrescriptionButton.disabled = true;
        return;
    }
    const maxBytes = 5 * 1024 * 1024;
    if (file.size > maxBytes) {
        showMessage(prescriptionActionStatus, "File size exceeds 5 MB. Please select a smaller file.");
        prescriptionActionStatus.className = "message message-error";
        prescriptionActionStatus.hidden = false;
        prescriptionFileInput.value = "";
        selectedPrescriptionFile = null;
        selectedFilePreview.hidden = true;
        uploadPrescriptionButton.disabled = true;
        return;
    }
    selectedPrescriptionFile = file;
    selectedFilePreview.hidden = false;
    const sizeKB = (file.size / 1024).toFixed(1);
    selectedFilePreview.textContent = `Selected: ${file.name} (${sizeKB} KB)`;
    uploadPrescriptionButton.disabled = false;
    prescriptionActionStatus.hidden = true;
}

if (prescriptionFileInput) {
    prescriptionFileInput.addEventListener("change", (e) => {
        const file = e.target.files && e.target.files[0];
        handleSelectedPrescriptionFile(file);
    });
}

// Drag & drop dropzone events
if (rxDropzone) {
    rxDropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        rxDropzone.classList.add("is-dragover");
    });
    rxDropzone.addEventListener("dragleave", () => {
        rxDropzone.classList.remove("is-dragover");
    });
    rxDropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        rxDropzone.classList.remove("is-dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length) {
            prescriptionFileInput.files = e.dataTransfer.files;
            handleSelectedPrescriptionFile(e.dataTransfer.files[0]);
        }
    });
}

// Upload Prescription Submit
if (prescriptionUploadForm) {
    prescriptionUploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedBill || !selectedPrescriptionFile) return;

        const doctorName = doctorNameInput.value.trim();
        const doctorRegNo = doctorRegNoInput.value.trim();

        if (selectedBill.requires_prescription && (!doctorName || !doctorRegNo)) {
            showMessage(prescriptionActionStatus, "Doctor Name and Registration Number are required for Schedule H medicines.");
            prescriptionActionStatus.className = "message message-error";
            prescriptionActionStatus.hidden = false;
            if (!doctorName) doctorNameInput.focus();
            else doctorRegNoInput.focus();
            return;
        }

        uploadPrescriptionButton.disabled = true;
        uploadPrescriptionButton.textContent = "Uploading…";
        prescriptionActionStatus.hidden = true;

        const formData = new FormData();
        formData.append("file", selectedPrescriptionFile);
        if (doctorName) formData.append("doctor_name", doctorName);
        if (doctorRegNo) formData.append("doctor_reg_no", doctorRegNo);

        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${API_BASE_URL}/api/v1/bills/${encodeURIComponent(selectedBill.id)}/prescription`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                },
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to upload prescription.");
            }

            const updated = await res.json();
            selectedBill = updated;
            renderBillDetails();
            await loadBills();

            prescriptionUploadForm.reset();
            selectedPrescriptionFile = null;
            selectedFilePreview.hidden = true;
            uploadPrescriptionButton.disabled = true;

            showMessage(prescriptionActionStatus, "Prescription successfully attached to this bill.");
            prescriptionActionStatus.className = "message message-success";
            prescriptionActionStatus.hidden = false;
            setTimeout(() => { prescriptionActionStatus.hidden = true; }, 4000);
        } catch (err) {
            showMessage(prescriptionActionStatus, err.message);
            prescriptionActionStatus.className = "message message-error";
            prescriptionActionStatus.hidden = false;
        } finally {
            uploadPrescriptionButton.disabled = false;
            uploadPrescriptionButton.textContent = "Attach prescription to bill";
        }
    });
}

// Remove Prescription
if (removePrescriptionBtn) {
    removePrescriptionBtn.addEventListener("click", async () => {
        if (!selectedBill || !selectedBill.prescription) return;
        const confirmed = await window.showConfirmDialog({
            title: "Remove prescription?",
            message: "Are you sure you want to remove the attached doctor prescription from this draft bill?",
            confirmText: "Remove prescription",
            variant: "danger"
        });
        if (!confirmed) return;

        try {
            const updated = await apiRequest(`/api/v1/bills/${encodeURIComponent(selectedBill.id)}/prescription`, {
                method: "DELETE"
            });
            selectedBill = updated;
            renderBillDetails();
            await loadBills();
            showMessage(prescriptionActionStatus, "Prescription removed.");
            prescriptionActionStatus.className = "message message-success";
            prescriptionActionStatus.hidden = false;
            setTimeout(() => { prescriptionActionStatus.hidden = true; }, 3000);
        } catch (err) {
            showMessage(prescriptionActionStatus, err.message);
            prescriptionActionStatus.className = "message message-error";
            prescriptionActionStatus.hidden = false;
        }
    });
}

// View Prescription Modal
if (viewPrescriptionBtn) {
    viewPrescriptionBtn.addEventListener("click", () => {
        if (!selectedBill || !selectedBill.prescription) return;
        const rx = selectedBill.prescription;
        rxModalTitle.textContent = `Prescription for ${selectedBill.invoice_number}`;
        const docParts = [];
        if (rx.doctor_name) docParts.push(`Dr. ${rx.doctor_name}`);
        if (rx.doctor_reg_no) docParts.push(`Reg No: ${rx.doctor_reg_no}`);
        rxModalSubtitle.textContent = docParts.join(" · ") || rx.file_name;

        const fullUrl = `${API_BASE_URL}${rx.file_path}`;
        if (rxPdfLink) rxPdfLink.href = fullUrl;

        const isPdf = rx.content_type === "application/pdf" || (rx.file_name && rx.file_name.toLowerCase().endsWith(".pdf"));
        if (rxImageContainer) rxImageContainer.hidden = isPdf;
        if (rxPdfContainer) rxPdfContainer.hidden = !isPdf;
        if (rxModalImage) rxModalImage.src = isPdf ? "" : fullUrl;

        prescriptionModal.hidden = false;
    });
}

function closePrescriptionModal() {
    if (prescriptionModal) prescriptionModal.hidden = true;
    if (rxModalImage) rxModalImage.src = "";
    if (rxImageContainer) rxImageContainer.hidden = true;
    if (rxPdfContainer) rxPdfContainer.hidden = true;
}

if (closeRxModalBtn) closeRxModalBtn.addEventListener("click", closePrescriptionModal);
if (rxModalBackdrop) rxModalBackdrop.addEventListener("click", closePrescriptionModal);
window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && prescriptionModal && !prescriptionModal.hidden) {
        closePrescriptionModal();
    }
});

// ==========================================================================
// Add-on 3: Barcode & QR Code Checkout Scanner
// ==========================================================================

function showBarcodeFeedback(text, type = "success") {
    if (!barcodeScanFeedback) return;
    barcodeScanFeedback.textContent = text;
    barcodeScanFeedback.className = `barcode-feedback is-${type}`;
    barcodeScanFeedback.hidden = false;
    window.clearTimeout(barcodeScanFeedback._timer);
    barcodeScanFeedback._timer = window.setTimeout(() => {
        barcodeScanFeedback.hidden = true;
    }, 4500);
}

function playScanBeep() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(1400, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.12);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.13);
    } catch {
        // AudioContext not supported or restricted
    }
}

async function processScannedCode(rawCode) {
    if (!selectedBill || selectedBill.status !== "draft") {
        showBarcodeFeedback("Open an active draft bill first before scanning medicines.", "error");
        return;
    }

    const code = (rawCode || "").trim();
    if (!code) return;

    const now = Date.now();
    if (code === lastScannedCode && now - lastScanTimestamp < 1200) {
        return;
    }
    lastScannedCode = code;
    lastScanTimestamp = now;

    try {
        const med = await apiRequest(`/api/v1/medicines/barcode/${encodeURIComponent(code)}`);
        playScanBeep();

        if (med.stock <= 0) {
            showBarcodeFeedback(`⚠️ ${med.name} (SKU: ${med.sku || 'N/A'}): Out of stock! (Available: 0)`, "error");
            return;
        }

        const autoAdd = autoAddScanCheckbox ? autoAddScanCheckbox.checked : true;

        if (autoAdd) {
            const existingItem = (selectedBill.items || []).find((it) => it.medicine_id === med.id);
            if (existingItem) {
                const newQty = existingItem.quantity + 1;
                if (newQty > med.stock) {
                    showBarcodeFeedback(`⚠️ Stock limit reached for ${med.name} (Current: ${existingItem.quantity}, Stock: ${med.stock}).`, "error");
                    return;
                }
                await apiRequest(`/api/v1/bills/items/${encodeURIComponent(existingItem.id)}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ quantity: newQty })
                });
                showBarcodeFeedback(`✓ Incremented ${med.name} quantity to ${newQty}.`, "success");
            } else {
                await apiRequest("/api/v1/bills/items", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        bill_id: selectedBill.id,
                        medicine_id: med.id,
                        quantity: 1
                    })
                });
                showBarcodeFeedback(`✓ Added ${med.name} (SKU: ${med.sku || code}) to bill.`, "success");
            }

            await openBill(selectedBill.id, false);
            await loadBills();
        } else {
            medicineSelect.value = med.id;
            quantityInput.value = "1";
            quantityInput.max = String(med.stock);
            showBarcodeFeedback(`✓ Selected ${med.name} (${formatMoney(med.price)}). Specify quantity and click Add.`, "success");
            quantityInput.focus();
        }

        if (barcodeInput) barcodeInput.value = "";
    } catch (err) {
        showBarcodeFeedback(err.message || `No medicine found for barcode '${code}'.`, "error");
    }
}

// Hardware Barcode Scanner HID key listener (rapid key sequence)
let hwBarcodeBuffer = "";
let hwLastKeyTime = 0;

window.addEventListener("keydown", (e) => {
    if (!selectedBill || selectedBill.status !== "draft") return;

    const isBarcodeFocused = document.activeElement === barcodeInput;
    const isOtherInputFocused = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName) && !isBarcodeFocused;

    const now = Date.now();
    const interval = now - hwLastKeyTime;
    hwLastKeyTime = now;

    if (e.key === "Enter") {
        if (hwBarcodeBuffer.length >= 2 && interval < 60) {
            e.preventDefault();
            const scanned = hwBarcodeBuffer;
            hwBarcodeBuffer = "";
            processScannedCode(scanned);
        } else {
            hwBarcodeBuffer = "";
        }
        return;
    }

    if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
        if (interval < 50 || hwBarcodeBuffer.length === 0) {
            if (!isOtherInputFocused) {
                hwBarcodeBuffer += e.key;
            }
        } else {
            hwBarcodeBuffer = isOtherInputFocused ? "" : e.key;
        }
    }
});

// Barcode manual input events
if (barcodeInput) {
    barcodeInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const code = barcodeInput.value.trim();
            if (code) processScannedCode(code);
        }
    });
}

if (barcodeLookupBtn) {
    barcodeLookupBtn.addEventListener("click", () => {
        const code = barcodeInput ? barcodeInput.value.trim() : "";
        if (code) processScannedCode(code);
    });
}

// Camera Scanner Handling
async function startCameraScanner() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Camera scanner is not supported on this browser or requires HTTPS / localhost.");
        return;
    }

    if (scannerModal) scannerModal.hidden = false;
    if (scannerStatusBadge) scannerStatusBadge.textContent = "Connecting camera…";

    try {
        if (activeScannerStream) {
            activeScannerStream.getTracks().forEach((track) => track.stop());
        }

        activeScannerStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: currentFacingMode },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });

        if (scannerVideo) {
            scannerVideo.srcObject = activeScannerStream;
            await scannerVideo.play();
        }

        if (scannerStatusBadge) {
            scannerStatusBadge.textContent = "Camera active. Center barcode inside the green box.";
        }

        const track = activeScannerStream.getVideoTracks()[0];
        const capabilities = track.getCapabilities ? track.getCapabilities() : {};
        if (toggleTorchBtn) {
            toggleTorchBtn.hidden = !capabilities.torch;
        }

        startBarcodeDetectionLoop();
    } catch (err) {
        if (scannerStatusBadge) {
            scannerStatusBadge.textContent = `Camera error: ${err.message}`;
        }
    }
}

function stopCameraScanner() {
    if (scannerAnimFrameId) {
        window.cancelAnimationFrame(scannerAnimFrameId);
        scannerAnimFrameId = null;
    }
    if (activeScannerStream) {
        activeScannerStream.getTracks().forEach((track) => track.stop());
        activeScannerStream = null;
    }
    if (scannerVideo) scannerVideo.srcObject = null;
    if (scannerModal) scannerModal.hidden = true;
    isTorchOn = false;
    if (toggleTorchBtn) toggleTorchBtn.textContent = "🔦 Torch";
}

async function startBarcodeDetectionLoop() {
    if ("BarcodeDetector" in window) {
        try {
            const formats = ["ean_13", "ean_8", "code_128", "code_39", "qr_code", "upc_a", "upc_e"];
            const detector = new window.BarcodeDetector({ formats });

            const scanFrame = async () => {
                if (!activeScannerStream || !scannerVideo || scannerVideo.readyState < 2) {
                    scannerAnimFrameId = window.requestAnimationFrame(scanFrame);
                    return;
                }

                try {
                    const barcodes = await detector.detect(scannerVideo);
                    if (barcodes && barcodes.length > 0) {
                        const raw = barcodes[0].rawValue;
                        if (raw) {
                            if (scannerStatusBadge) {
                                scannerStatusBadge.textContent = `✓ Detected: ${raw}`;
                            }
                            await processScannedCode(raw);
                        }
                    }
                } catch {
                    // detection frame error
                }

                scannerAnimFrameId = window.requestAnimationFrame(scanFrame);
            };

            scannerAnimFrameId = window.requestAnimationFrame(scanFrame);
            return;
        } catch {
            // fallback if format unsupported
        }
    }

    if (scannerStatusBadge) {
        scannerStatusBadge.textContent = "Align barcode with camera or use manual scan input.";
    }
}

if (openCameraScannerButton) openCameraScannerButton.addEventListener("click", startCameraScanner);
if (closeScannerModalBtn) closeScannerModalBtn.addEventListener("click", stopCameraScanner);
if (scannerModalBackdrop) scannerModalBackdrop.addEventListener("click", stopCameraScanner);

if (switchCameraBtn) {
    switchCameraBtn.addEventListener("click", async () => {
        currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
        await startCameraScanner();
    });
}

if (toggleTorchBtn) {
    toggleTorchBtn.addEventListener("click", async () => {
        if (!activeScannerStream) return;
        const track = activeScannerStream.getVideoTracks()[0];
        if (track && track.applyConstraints) {
            isTorchOn = !isTorchOn;
            await track.applyConstraints({ advanced: [{ torch: isTorchOn }] });
            toggleTorchBtn.textContent = isTorchOn ? "🔦 Turn off" : "🔦 Torch";
        }
    });
}

window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && scannerModal && !scannerModal.hidden) {
        stopCameraScanner();
    }
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

        const tasks = [
            loadBills(false),
            apiRequest("/api/v1/settings/store").then((res) => { storeSettings = res || {}; }).catch(() => {})
        ];
        if (permissions.includes("bill:create")) {
            createBillSection.hidden = false;
            const initialSearchId = ++medicineSearchRequestId;
            tasks.push(searchMedicines("", initialSearchId));
        }

        await Promise.all(tasks);

    } catch (error) {
        showMessage(errorMessage, error.message);
        statusMessage.hidden = true;

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();
