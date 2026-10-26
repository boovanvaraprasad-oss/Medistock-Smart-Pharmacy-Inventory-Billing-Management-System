const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const clearButton = document.getElementById("clearButton");
const previousButton = document.getElementById("previousButton");
const nextButton = document.getElementById("nextButton");
const statusMessage = document.getElementById("statusMessage");
const pageMessage = document.getElementById("pageMessage");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const medicineRows = document.getElementById("medicineRows");
const pageInfo = document.getElementById("pageInfo");

const createMedicineSection = document.getElementById("createMedicineSection");
const createMedicineForm = document.getElementById("createMedicineForm");
const createMedicineButton = document.getElementById("createMedicineButton");
const cancelEditButton = document.getElementById("cancelEditButton");
const medicineFormTitle = document.getElementById("medicineFormTitle");

const pageSize = 20;
let currentPage = 1;
let currentSearch = "";
let canWriteMedicines = false;
let editingMedicineId = null;
let referencesAvailable = true;

const numberFormatter = new Intl.NumberFormat("en-IN");
const currencyFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
});

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

function displayMedicines(medicines) {
    medicineRows.replaceChildren();

    for (const medicine of medicines) {
        const row = document.createElement("tr");

        addCell(row, medicine.name || "—");
        addCell(row, medicine.sku || "—");
        addCell(row, medicine.dosage_form || "—");
        addCell(row, numberFormatter.format(medicine.stock ?? 0));
        addCell(row, currencyFormatter.format(medicine.price ?? 0));
        addCell(row, numberFormatter.format(medicine.reorder_threshold ?? 0));
        addCell(row, medicine.is_active ? "Active" : "Inactive");

        const actionsCell = addCell(row, "");

        if (canWriteMedicines) {
            const actions = document.createElement("div");
            actions.className = "row-actions";

            const editButton = document.createElement("button");
            editButton.className = "button button-secondary";
            editButton.type = "button";
            editButton.textContent = "Edit";
            editButton.addEventListener("click", () => startEditingMedicine(medicine));

            const statusButton = document.createElement("button");
            statusButton.className = "button button-secondary";
            statusButton.type = "button";
            statusButton.textContent = medicine.is_active ? "Deactivate" : "Activate";
            statusButton.addEventListener("click", () => toggleMedicineStatus(medicine));

            actions.append(editButton, statusButton);
            actionsCell.appendChild(actions);
        } else {
            actionsCell.textContent = "—";
        }

        medicineRows.appendChild(row);
    }
}

async function loadMedicines() {
    statusMessage.textContent = "Loading medicines…";
    statusMessage.hidden = false;
    errorMessage.hidden = true;
    previousButton.disabled = true;
    nextButton.disabled = true;

    const parameters = new URLSearchParams({
        page: String(currentPage),
        limit: String(pageSize)
    });

    if (currentSearch) {
        parameters.set("search", currentSearch);
    }

    try {
        const result = await apiRequest(`/api/v1/medicines?${parameters.toString()}`);
        displayMedicines(result.items);

        const totalPages = Math.max(1, Math.ceil(result.total / result.limit));
        pageInfo.textContent =
            `Page ${result.page} of ${totalPages} · ${result.total} medicines`;

        previousButton.disabled = result.page <= 1;
        nextButton.disabled = result.page >= totalPages;

        statusMessage.textContent = result.total === 0 ? "No medicines found." : "";
        statusMessage.hidden = result.total !== 0;
    } catch (error) {
        statusMessage.hidden = true;
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

function fillSelect(selectId, records, placeholder) {
    const select = document.getElementById(selectId);
    select.replaceChildren();

    const firstOption = document.createElement("option");
    firstOption.value = "";
    firstOption.textContent = placeholder;
    select.appendChild(firstOption);

    const activeRecords = records.filter((record) => record.is_active);

    for (const record of activeRecords) {
        const option = document.createElement("option");
        option.value = record.id;
        option.textContent = record.name;
        select.appendChild(option);
    }

    select.disabled = activeRecords.length === 0;
    return activeRecords.length > 0;
}

async function loadMedicineReferences() {
    const [categories, manufacturers, units, suppliers] = await Promise.all([
        apiRequest("/api/v1/categories"),
        apiRequest("/api/v1/manufacturers"),
        apiRequest("/api/v1/units"),
        apiRequest("/api/v1/suppliers")
    ]);

    const hasCategories = fillSelect("medicineCategory", categories, "Choose category");
    const hasManufacturers = fillSelect(
        "medicineManufacturer",
        manufacturers,
        "Choose manufacturer"
    );
    const hasUnits = fillSelect("medicineUnit", units, "Choose unit");
    const hasSuppliers = fillSelect("medicineSupplier", suppliers, "Choose supplier");

    referencesAvailable =
        hasCategories && hasManufacturers && hasUnits && hasSuppliers;

    createMedicineButton.disabled = !referencesAvailable;

    if (!referencesAvailable) {
        showMessage(
            pageMessage,
            "Add at least one active category, manufacturer, unit, and supplier before creating a medicine."
        );
    }
}

function startEditingMedicine(medicine) {
    editingMedicineId = medicine.id;

    document.getElementById("medicineName").value = medicine.name || "";
    document.getElementById("medicineSku").value = medicine.sku || "";
    document.getElementById("medicineDosageForm").value = medicine.dosage_form || "";
    document.getElementById("medicinePrice").value = medicine.price ?? "";
    document.getElementById("medicineReorderThreshold").value =
        medicine.reorder_threshold ?? 10;
    document.getElementById("controlledSubstance").checked =
        Boolean(medicine.is_controlled_substance);

    // The linked category, manufacturer, unit, and supplier remain unchanged.
    for (const id of [
        "medicineCategory",
        "medicineManufacturer",
        "medicineUnit",
        "medicineSupplier"
    ]) {
        document.getElementById(id).disabled = true;
    }

    medicineFormTitle.textContent = "Edit medicine";
    createMedicineButton.textContent = "Save changes";
    createMedicineButton.disabled = false;
    cancelEditButton.hidden = false;
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    createMedicineSection.scrollIntoView({ behavior: "smooth" });
}

function stopEditingMedicine() {
    editingMedicineId = null;
    createMedicineForm.reset();

    for (const id of [
        "medicineCategory",
        "medicineManufacturer",
        "medicineUnit",
        "medicineSupplier"
    ]) {
        const select = document.getElementById(id);
        select.disabled = !select.options.length || select.options.length === 1;
    }

    document.getElementById("medicineReorderThreshold").value = "10";
    medicineFormTitle.textContent = "Add medicine";
    createMedicineButton.textContent = "Create medicine";
    createMedicineButton.disabled = !referencesAvailable;
    cancelEditButton.hidden = true;
}

async function toggleMedicineStatus(medicine) {
    const action = medicine.is_active ? "deactivate" : "activate";

    if (medicine.is_active && !(await window.showConfirmDialog({
        title: "Deactivate medicine?",
        message: `“${medicine.name}” will no longer be available for new sales. Its stock and history will be kept, and you can reactivate it later.`
    }))) {
        return;
    }

    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(`/api/v1/medicines/${medicine.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: !medicine.is_active })
        });

        showMessage(successMessage, `${medicine.name} was ${action}d.`);
        await loadMedicines();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

async function initializeMedicinePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await getCurrentUser();
        const permissions = currentUser.permissions || [];
        canWriteMedicines = permissions.includes("medicine:write");

        if (canWriteMedicines) {
            createMedicineSection.hidden = false;

            try {
                await loadMedicineReferences();
            } catch (error) {
                referencesAvailable = false;
                createMedicineButton.disabled = true;
                showMessage(errorMessage, error.message);
            }
        }

        await loadMedicines();
    } catch (error) {
        showMessage(errorMessage, error.message);

        if (!localStorage.getItem("access_token")) {
            window.location.href = "/";
        }
    }
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    currentSearch = searchInput.value.trim();
    currentPage = 1;
    loadMedicines();
});

clearButton.addEventListener("click", () => {
    searchInput.value = "";
    currentSearch = "";
    currentPage = 1;
    loadMedicines();
});

previousButton.addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage -= 1;
        loadMedicines();
    }
});

nextButton.addEventListener("click", () => {
    currentPage += 1;
    loadMedicines();
});

createMedicineForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    createMedicineButton.disabled = true;

    const isEditing = Boolean(editingMedicineId);
    const requestBody = {
        name: document.getElementById("medicineName").value.trim(),
        sku: document.getElementById("medicineSku").value.trim(),
        dosage_form: document.getElementById("medicineDosageForm").value.trim(),
        price: Number(document.getElementById("medicinePrice").value),
        reorder_threshold: Number(
            document.getElementById("medicineReorderThreshold").value
        ),
        is_controlled_substance:
            document.getElementById("controlledSubstance").checked
    };

    if (!isEditing) {
        requestBody.category_id = document.getElementById("medicineCategory").value;
        requestBody.manufacturer_id =
            document.getElementById("medicineManufacturer").value;
        requestBody.unit_id = document.getElementById("medicineUnit").value;
        requestBody.supplier_id = document.getElementById("medicineSupplier").value;
    }

    try {
        const url = isEditing
            ? `/api/v1/medicines/${editingMedicineId}`
            : "/api/v1/medicines";

        await apiRequest(url, {
            method: isEditing ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        showMessage(
            successMessage,
            isEditing
                ? "Medicine changes saved."
                : "Medicine created. Its starting stock is 0."
        );

        stopEditingMedicine();
        await loadMedicines();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        createMedicineButton.disabled = isEditing
            ? false
            : !referencesAvailable;
    }
});

cancelEditButton.addEventListener("click", stopEditingMedicine);

initializeMedicinePage();
