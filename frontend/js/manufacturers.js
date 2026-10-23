const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const statusMessage = document.getElementById("statusMessage");
const listDescription = document.getElementById("listDescription");
const manufacturerRows = document.getElementById("manufacturerRows");
const formSection = document.getElementById("formSection");
const manufacturerForm = document.getElementById("manufacturerForm");
const manufacturerName = document.getElementById("manufacturerName");
const formTitle = document.getElementById("formTitle");
const saveButton = document.getElementById("saveButton");
const cancelButton = document.getElementById("cancelButton");
const refreshButton = document.getElementById("refreshButton");

let permissions = [];
let editingManufacturer = null;

function showMessage(element, message) {
    element.textContent = message;
    element.hidden = !message;
}

function addCell(row, text) {
    const cell = document.createElement("td");
    cell.textContent = text;
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

async function loadManufacturers() {
    statusMessage.textContent = "Loading manufacturers…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        const manufacturers = await apiRequest("/api/v1/manufacturers");
        renderManufacturers(manufacturers);
        listDescription.textContent = `${manufacturers.length} manufacturers`;
        statusMessage.textContent = manufacturers.length
            ? ""
            : "No manufacturers found.";
        statusMessage.hidden = manufacturers.length > 0;
    } catch (error) {
        statusMessage.hidden = true;
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

function renderManufacturers(manufacturers) {
    manufacturerRows.replaceChildren();

    if (manufacturers.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 3;
        cell.textContent = "No manufacturers found.";
        row.appendChild(cell);
        manufacturerRows.appendChild(row);
        return;
    }

    for (const manufacturer of manufacturers) {
        const row = document.createElement("tr");
        addCell(row, manufacturer.name);

        const statusCell = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = `status-pill ${
            manufacturer.is_active ? "status-active" : "status-inactive"
        }`;
        statusPill.textContent = manufacturer.is_active ? "Active" : "Inactive";
        statusCell.appendChild(statusPill);
        row.appendChild(statusCell);

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "row-actions";

        if (permissions.includes("medicine:write")) {
            actions.appendChild(makeButton(
                "Edit",
                "button button-secondary button-small",
                () => startEditing(manufacturer)
            ));

            actions.appendChild(makeButton(
                manufacturer.is_active ? "Deactivate" : "Activate",
                "button button-secondary button-small",
                () => toggleStatus(manufacturer)
            ));
        }

        if (permissions.includes("master_data:delete")) {
            actions.appendChild(makeButton(
                "Delete permanently",
                "button button-danger button-small",
                () => deleteManufacturer(manufacturer)
            ));
        }

        actionsCell.appendChild(actions);
        if (!actions.childElementCount) {
            actionsCell.textContent = "—";
        }
        row.appendChild(actionsCell);

        manufacturerRows.appendChild(row);
    }
}

function startEditing(manufacturer) {
    editingManufacturer = manufacturer;
    manufacturerName.value = manufacturer.name;
    formTitle.textContent = "Edit manufacturer";
    saveButton.textContent = "Save changes";
    cancelButton.hidden = false;
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    formSection.scrollIntoView({ behavior: "smooth" });
    manufacturerName.focus();
}

function resetForm() {
    editingManufacturer = null;
    manufacturerForm.reset();
    formTitle.textContent = "Add manufacturer";
    saveButton.textContent = "Create manufacturer";
    cancelButton.hidden = true;
}

async function toggleStatus(manufacturer) {
    const activating = !manufacturer.is_active;

    if (!activating && !(await window.showConfirmDialog({
        title: "Deactivate manufacturer?",
        message: `“${manufacturer.name}” will no longer be available for new selections. Existing medicine records will be kept, and you can reactivate it later.`
    }))) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(
            `/api/v1/manufacturers/${encodeURIComponent(manufacturer.id)}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: activating })
            }
        );

        showMessage(
            successMessage,
            activating ? "Manufacturer activated." : "Manufacturer deactivated."
        );
        await loadManufacturers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

async function deleteManufacturer(manufacturer) {
    const confirmed = await window.showConfirmDialog({
        title: "Delete manufacturer permanently?",
        message: `“${manufacturer.name}” will be permanently removed. This cannot be undone, and deletion may be blocked if medicines are linked to this manufacturer.`,
        confirmText: "Delete permanently"
    });

    if (!confirmed) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        const result = await apiRequest(
            `/api/v1/manufacturers/${encodeURIComponent(manufacturer.id)}`,
            { method: "DELETE" }
        );

        showMessage(successMessage, result.message || "Manufacturer deleted.");
        await loadManufacturers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

manufacturerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    saveButton.disabled = true;

    const isEditing = Boolean(editingManufacturer);
    const url = isEditing
        ? `/api/v1/manufacturers/${encodeURIComponent(editingManufacturer.id)}`
        : "/api/v1/manufacturers";

    try {
        await apiRequest(url, {
            method: isEditing ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: manufacturerName.value.trim() })
        });

        showMessage(
            successMessage,
            isEditing ? "Manufacturer changes saved." : "Manufacturer created."
        );
        resetForm();
        await loadManufacturers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        saveButton.disabled = false;
    }
});

cancelButton.addEventListener("click", resetForm);
refreshButton.addEventListener("click", loadManufacturers);

async function initializePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        permissions = currentUser.permissions || [];

        if (permissions.includes("medicine:write")) {
            formSection.hidden = false;
        }

        await loadManufacturers();
    } catch (error) {
        showMessage(errorMessage, error.message);
        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();
