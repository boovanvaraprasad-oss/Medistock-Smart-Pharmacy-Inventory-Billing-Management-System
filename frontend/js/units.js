const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const statusMessage = document.getElementById("statusMessage");
const listDescription = document.getElementById("listDescription");
const unitRows = document.getElementById("unitRows");
const formSection = document.getElementById("formSection");
const unitForm = document.getElementById("unitForm");
const unitName = document.getElementById("unitName");
const formTitle = document.getElementById("formTitle");
const saveButton = document.getElementById("saveButton");
const cancelButton = document.getElementById("cancelButton");
const refreshButton = document.getElementById("refreshButton");

let permissions = [];
let editingUnit = null;

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

async function loadUnits() {
    statusMessage.textContent = "Loading units…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        const units = await apiRequest("/api/v1/units");
        renderUnits(units);
        listDescription.textContent = `${units.length} units`;
        statusMessage.textContent = units.length ? "" : "No units found.";
        statusMessage.hidden = units.length > 0;
    } catch (error) {
        statusMessage.hidden = true;
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

function renderUnits(units) {
    unitRows.replaceChildren();

    if (units.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 3;
        cell.textContent = "No units found.";
        row.appendChild(cell);
        unitRows.appendChild(row);
        return;
    }

    for (const unit of units) {
        const row = document.createElement("tr");
        addCell(row, unit.name);

        const statusCell = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = `status-pill ${
            unit.is_active ? "status-active" : "status-inactive"
        }`;
        statusPill.textContent = unit.is_active ? "Active" : "Inactive";
        statusCell.appendChild(statusPill);
        row.appendChild(statusCell);

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "row-actions";

        if (permissions.includes("medicine:write")) {
            actions.appendChild(makeButton(
                "Edit",
                "button button-secondary button-small",
                () => startEditing(unit)
            ));

            actions.appendChild(makeButton(
                unit.is_active ? "Deactivate" : "Activate",
                "button button-secondary button-small",
                () => toggleStatus(unit)
            ));
        }

        if (permissions.includes("master_data:delete")) {
            actions.appendChild(makeButton(
                "Delete permanently",
                "button button-danger button-small",
                () => deleteUnit(unit)
            ));
        }

        actionsCell.appendChild(actions);
        if (!actions.childElementCount) {
            actionsCell.textContent = "—";
        }
        row.appendChild(actionsCell);

        unitRows.appendChild(row);
    }
}

function startEditing(unit) {
    editingUnit = unit;
    unitName.value = unit.name;
    formTitle.textContent = "Edit unit";
    saveButton.textContent = "Save changes";
    cancelButton.hidden = false;
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    formSection.scrollIntoView({ behavior: "smooth" });
    unitName.focus();
}

function resetForm() {
    editingUnit = null;
    unitForm.reset();
    formTitle.textContent = "Add unit";
    saveButton.textContent = "Create unit";
    cancelButton.hidden = true;
}

async function toggleStatus(unit) {
    const activating = !unit.is_active;

    if (!activating && !(await window.showConfirmDialog({
        title: "Deactivate unit?",
        message: `“${unit.name}” will no longer be available for new selections. Existing records will be kept, and you can reactivate it later.`
    }))) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(`/api/v1/units/${encodeURIComponent(unit.id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: activating })
        });

        showMessage(
            successMessage,
            activating ? "Unit activated." : "Unit deactivated."
        );
        await loadUnits();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

async function deleteUnit(unit) {
    const confirmed = await window.showConfirmDialog({
        title: "Delete unit permanently?",
        message: `“${unit.name}” will be permanently removed. This cannot be undone, and deletion may be blocked if the unit is still in use.`,
        confirmText: "Delete permanently"
    });

    if (!confirmed) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        const result = await apiRequest(
            `/api/v1/units/${encodeURIComponent(unit.id)}`,
            { method: "DELETE" }
        );

        showMessage(successMessage, result.message || "Unit deleted.");
        await loadUnits();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

unitForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    saveButton.disabled = true;

    const isEditing = Boolean(editingUnit);
    const url = isEditing
        ? `/api/v1/units/${encodeURIComponent(editingUnit.id)}`
        : "/api/v1/units";

    try {
        await apiRequest(url, {
            method: isEditing ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: unitName.value.trim() })
        });

        showMessage(
            successMessage,
            isEditing ? "Unit changes saved." : "Unit created."
        );
        resetForm();
        await loadUnits();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        saveButton.disabled = false;
    }
});

cancelButton.addEventListener("click", resetForm);
refreshButton.addEventListener("click", loadUnits);

async function initializePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await getCurrentUser();
        permissions = currentUser.permissions || [];

        if (permissions.includes("medicine:write")) {
            formSection.hidden = false;
        }

        await loadUnits();
    } catch (error) {
        showMessage(errorMessage, error.message);
        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();
