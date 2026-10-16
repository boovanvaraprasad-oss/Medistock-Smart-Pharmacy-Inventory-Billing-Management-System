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

const pageSize = 20;
let currentPage = 1;
let currentSearch = "";

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
        addCell(
            row,
            numberFormatter.format(medicine.reorder_threshold ?? 0)
        );
        addCell(row, medicine.is_active ? "Active" : "Inactive");

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
        const result = await apiRequest(
            `/api/v1/medicines?${parameters.toString()}`
        );

        displayMedicines(result.items);

        const totalPages = Math.max(
            1,
            Math.ceil(result.total / result.limit)
        );

        pageInfo.textContent =
            `Page ${result.page} of ${totalPages} · ${result.total} medicines`;

        previousButton.disabled = result.page <= 1;
        nextButton.disabled = result.page >= totalPages;

        statusMessage.textContent = result.total === 0
            ? "No medicines found."
            : "";
        statusMessage.hidden = result.total !== 0;
    } catch (error) {
        statusMessage.hidden = true;
        errorMessage.textContent = error.message;
        errorMessage.hidden = false;

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

    const hasCategories = fillSelect(
        "medicineCategory",
        categories,
        "Choose category"
    );
    const hasManufacturers = fillSelect(
        "medicineManufacturer",
        manufacturers,
        "Choose manufacturer"
    );
    const hasUnits = fillSelect(
        "medicineUnit",
        units,
        "Choose unit"
    );
    const hasSuppliers = fillSelect(
        "medicineSupplier",
        suppliers,
        "Choose supplier"
    );

    const referencesAvailable =
        hasCategories && hasManufacturers && hasUnits && hasSuppliers;

    createMedicineButton.disabled = !referencesAvailable;

    if (!referencesAvailable) {
        showMessage(
            pageMessage,
            "Add at least one active category, manufacturer, unit, and supplier before creating a medicine."
        );
    }
}

async function initializeMedicinePage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        const currentUser = await apiRequest("/api/v1/auth/me");
        const permissions = currentUser.permissions || [];

        if (permissions.includes("medicine:write")) {
            createMedicineSection.hidden = false;

            try {
                await loadMedicineReferences();
            } catch (error) {
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

    const requestBody = {
        name: document.getElementById("medicineName").value.trim(),
        sku: document.getElementById("medicineSku").value.trim(),
        dosage_form: document.getElementById("medicineDosageForm").value.trim(),
        category_id: document.getElementById("medicineCategory").value,
        manufacturer_id: document.getElementById("medicineManufacturer").value,
        unit_id: document.getElementById("medicineUnit").value,
        supplier_id: document.getElementById("medicineSupplier").value,
        price: Number(document.getElementById("medicinePrice").value),
        reorder_threshold: Number(
            document.getElementById("medicineReorderThreshold").value
        ),
        is_controlled_substance:
            document.getElementById("controlledSubstance").checked
    };

    try {
        const createdMedicine = await apiRequest("/api/v1/medicines", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        createMedicineForm.reset();
        document.getElementById("medicineReorderThreshold").value = "10";
        showMessage(
            successMessage,
            `${createdMedicine.name} was created. Its starting stock is 0.`
        );

        currentPage = 1;
        currentSearch = "";
        searchInput.value = "";
        await loadMedicines();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        createMedicineButton.disabled = false;
    }
});

initializeMedicinePage();