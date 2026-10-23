const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const statusMessage = document.getElementById("statusMessage");
const listDescription = document.getElementById("listDescription");
const supplierRows = document.getElementById("supplierRows");
const formSection = document.getElementById("formSection");
const supplierForm = document.getElementById("supplierForm");
const supplierName = document.getElementById("supplierName");
const supplierPhone = document.getElementById("supplierPhone");
const supplierEmail = document.getElementById("supplierEmail");
const supplierAddress = document.getElementById("supplierAddress");
const formTitle = document.getElementById("formTitle");
const saveButton = document.getElementById("saveButton");
const cancelButton = document.getElementById("cancelButton");
const refreshButton = document.getElementById("refreshButton");

let permissions = [];
let editingSupplier = null;

function showMessage(element, message) {
    element.textContent = message;
    element.hidden = !message;
}

function addCell(row, text) {
    const cell = document.createElement("td");
    cell.textContent = text || "—";
    row.appendChild(cell);
    return cell;
}

function makeButton(label, className, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
}

async function loadSuppliers() {
    statusMessage.textContent = "Loading suppliers…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        const suppliers = await apiRequest("/api/v1/suppliers");
        renderSuppliers(suppliers);
        listDescription.textContent = `${suppliers.length} suppliers`;
        statusMessage.textContent = suppliers.length ? "" : "No suppliers found.";
        statusMessage.hidden = suppliers.length > 0;
    } catch (error) {
        statusMessage.hidden = true;
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

function renderSuppliers(suppliers) {
    supplierRows.replaceChildren();

    if (suppliers.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.textContent = "No suppliers found.";
        row.appendChild(cell);
        supplierRows.appendChild(row);
        return;
    }

    for (const supplier of suppliers) {
        const row = document.createElement("tr");
        addCell(row, supplier.name);
        addCell(row, supplier.phone);
        addCell(row, supplier.email);
        addCell(row, supplier.address);

        const statusCell = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = `status-pill ${
            supplier.is_active ? "status-active" : "status-inactive"
        }`;
        statusPill.textContent = supplier.is_active ? "Active" : "Inactive";
        statusCell.appendChild(statusPill);
        row.appendChild(statusCell);

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "row-actions";

        if (permissions.includes("supplier:write")) {
            actions.appendChild(makeButton(
                "Edit",
                "button button-secondary button-small",
                () => startEditing(supplier)
            ));

            actions.appendChild(makeButton(
                supplier.is_active ? "Deactivate" : "Activate",
                "button button-secondary button-small",
                () => toggleStatus(supplier)
            ));
        }

        if (permissions.includes("master_data:delete")) {
            actions.appendChild(makeButton(
                "Delete permanently",
                "button button-danger button-small",
                () => deleteSupplier(supplier)
            ));
        }

        actionsCell.appendChild(actions);
        if (!actions.childElementCount) {
            actionsCell.textContent = "—";
        }
        row.appendChild(actionsCell);

        supplierRows.appendChild(row);
    }
}

function startEditing(supplier) {
    editingSupplier = supplier;
    supplierName.value = supplier.name || "";
    supplierPhone.value = supplier.phone || "";
    supplierEmail.value = supplier.email || "";
    supplierAddress.value = supplier.address || "";
    formTitle.textContent = "Edit supplier";
    saveButton.textContent = "Save changes";
    cancelButton.hidden = false;
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    formSection.scrollIntoView({ behavior: "smooth" });
    supplierName.focus();
}

function resetForm() {
    editingSupplier = null;
    supplierForm.reset();
    formTitle.textContent = "Add supplier";
    saveButton.textContent = "Create supplier";
    cancelButton.hidden = true;
}

async function toggleStatus(supplier) {
    const activating = !supplier.is_active;

    if (!activating && !(await window.showConfirmDialog({
        title: "Deactivate supplier?",
        message: `“${supplier.name}” will no longer be available for new purchase orders. Existing order history will be kept, and you can reactivate this supplier later.`
    }))) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(`/api/v1/suppliers/${encodeURIComponent(supplier.id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: activating })
        });

        showMessage(
            successMessage,
            activating ? "Supplier activated." : "Supplier deactivated."
        );
        await loadSuppliers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

async function deleteSupplier(supplier) {
    const confirmed = await window.showConfirmDialog({
        title: "Delete supplier permanently?",
        message: `“${supplier.name}” will be permanently removed. This cannot be undone, and deletion may be blocked if the supplier has linked records.`,
        confirmText: "Delete permanently"
    });

    if (!confirmed) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        const result = await apiRequest(
            `/api/v1/suppliers/${encodeURIComponent(supplier.id)}`,
            { method: "DELETE" }
        );

        showMessage(successMessage, result.message || "Supplier deleted.");
        await loadSuppliers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

supplierForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    saveButton.disabled = true;

    const isEditing = Boolean(editingSupplier);
    const requestBody = {
        name: supplierName.value.trim(),
        phone: supplierPhone.value.trim()
    };
    const email = supplierEmail.value.trim();
    const address = supplierAddress.value.trim();

    if (email) {
        requestBody.email = email;
    } else if (!isEditing) {
        requestBody.email = null;
    }

    if (address) {
        requestBody.address = address;
    } else if (!isEditing) {
        requestBody.address = null;
    }

    const url = isEditing
        ? `/api/v1/suppliers/${encodeURIComponent(editingSupplier.id)}`
        : "/api/v1/suppliers";

    try {
        await apiRequest(url, {
            method: isEditing ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        showMessage(
            successMessage,
            isEditing ? "Supplier changes saved." : "Supplier created."
        );
        resetForm();
        await loadSuppliers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        saveButton.disabled = false;
    }
});

cancelButton.addEventListener("click", resetForm);
refreshButton.addEventListener("click", loadSuppliers);

async function initializePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        permissions = currentUser.permissions || [];

        if (permissions.includes("supplier:write")) {
            formSection.hidden = false;
        }

        await loadSuppliers();
    } catch (error) {
        showMessage(errorMessage, error.message);
        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();
