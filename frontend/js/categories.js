const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const statusMessage = document.getElementById("statusMessage");
const listDescription = document.getElementById("listDescription");
const categoryRows = document.getElementById("categoryRows");
const categoryFormSection = document.getElementById("categoryFormSection");
const categoryForm = document.getElementById("categoryForm");
const categoryName = document.getElementById("categoryName");
const formTitle = document.getElementById("formTitle");
const saveButton = document.getElementById("saveButton");
const cancelButton = document.getElementById("cancelButton");
const refreshButton = document.getElementById("refreshButton");

let permissions = [];
let editingCategory = null;

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

function addCell(row, text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    row.appendChild(cell);
    return cell;
}

async function loadCategories() {
    statusMessage.textContent = "Loading categories…";
    statusMessage.hidden = false;
    showMessage(errorMessage, "");

    try {
        const categories = await apiRequest("/api/v1/categories");
        renderCategories(categories);
        listDescription.textContent = `${categories.length} categories`;
        statusMessage.textContent = categories.length
            ? ""
            : "No categories found.";
        statusMessage.hidden = categories.length > 0;
    } catch (error) {
        statusMessage.hidden = true;
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

function renderCategories(categories) {
    categoryRows.replaceChildren();

    if (categories.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 3;
        cell.textContent = "No categories found.";
        row.appendChild(cell);
        categoryRows.appendChild(row);
        return;
    }

    for (const category of categories) {
        const row = document.createElement("tr");
        addCell(row, category.name);

        const statusCell = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = `status-pill ${
            category.is_active ? "status-active" : "status-inactive"
        }`;
        statusPill.textContent = category.is_active ? "Active" : "Inactive";
        statusCell.appendChild(statusPill);
        row.appendChild(statusCell);

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");
        actions.className = "row-actions";

        if (permissions.includes("medicine:write")) {
            actions.appendChild(makeButton(
                "Edit",
                "button button-secondary button-small",
                () => startEditing(category)
            ));

            actions.appendChild(makeButton(
                category.is_active ? "Deactivate" : "Activate",
                "button button-secondary button-small",
                () => toggleCategoryStatus(category)
            ));
        }

        if (permissions.includes("master_data:delete")) {
            actions.appendChild(makeButton(
                "Delete permanently",
                "button button-danger button-small",
                () => deleteCategory(category)
            ));
        }

        actionsCell.appendChild(actions);
        if (!actions.childElementCount) {
            actionsCell.textContent = "—";
        }
        row.appendChild(actionsCell);

        categoryRows.appendChild(row);
    }
}

function startEditing(category) {
    editingCategory = category;
    categoryName.value = category.name;
    formTitle.textContent = "Edit category";
    saveButton.textContent = "Save changes";
    cancelButton.hidden = false;
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    categoryFormSection.scrollIntoView({ behavior: "smooth" });
    categoryName.focus();
}

function resetForm() {
    editingCategory = null;
    categoryForm.reset();
    formTitle.textContent = "Add category";
    saveButton.textContent = "Create category";
    cancelButton.hidden = true;
}

async function toggleCategoryStatus(category) {
    const activating = !category.is_active;

    if (!activating && !(await window.showConfirmDialog({
        title: "Deactivate category?",
        message: `“${category.name}” will no longer be available for new selections. Existing records will be kept, and you can reactivate it later.`
    }))) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(`/api/v1/categories/${encodeURIComponent(category.id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: activating })
        });

        showMessage(
            successMessage,
            activating ? "Category activated." : "Category deactivated."
        );
        await loadCategories();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

async function deleteCategory(category) {
    const confirmed = await window.showConfirmDialog({
        title: "Delete category permanently?",
        message: `“${category.name}” will be permanently removed. This cannot be undone, and deletion may be blocked if the category is still in use.`,
        confirmText: "Delete permanently"
    });

    if (!confirmed) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        const result = await apiRequest(
            `/api/v1/categories/${encodeURIComponent(category.id)}`,
            { method: "DELETE" }
        );

        showMessage(
            successMessage,
            result.message || "Category deleted."
        );
        await loadCategories();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

categoryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    saveButton.disabled = true;

    const name = categoryName.value.trim();
    const isEditing = Boolean(editingCategory);
    const url = isEditing
        ? `/api/v1/categories/${encodeURIComponent(editingCategory.id)}`
        : "/api/v1/categories";

    try {
        await apiRequest(url, {
            method: isEditing ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });

        showMessage(
            successMessage,
            isEditing ? "Category changes saved." : "Category created."
        );
        resetForm();
        await loadCategories();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        saveButton.disabled = false;
    }
});

cancelButton.addEventListener("click", resetForm);
refreshButton.addEventListener("click", loadCategories);

async function initializePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        permissions = currentUser.permissions || [];

        if (permissions.includes("medicine:write")) {
            categoryFormSection.hidden = false;
        }

        await loadCategories();
    } catch (error) {
        showMessage(errorMessage, error.message);
        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

initializePage();
