const themeToggle = document.getElementById("themeToggle");
const settingsStatus = document.getElementById("settingsStatus");
const billingSettingsCard = document.getElementById("billingSettingsCard");
const billingSettingsForm = document.getElementById("billingSettingsForm");
const defaultTaxPercentage = document.getElementById("defaultTaxPercentage");
const invoicePrefix = document.getElementById("invoicePrefix");
const billingSettingsStatus = document.getElementById("billingSettingsStatus");
const storeSettingsCard = document.getElementById("storeSettingsCard");
const storeSettingsForm = document.getElementById("storeSettingsForm");
const storeSettingsStatus = document.getElementById("storeSettingsStatus");
const storeSettingsSaveButton = document.getElementById("storeSettingsSaveButton");
const storeFields = {
    store_name: document.getElementById("storeName"),
    address: document.getElementById("storeAddress"),
    phone: document.getElementById("storePhone"),
    email: document.getElementById("storeEmail"),
    license_number: document.getElementById("storeLicenseNumber")
};

themeToggle.checked = localStorage.getItem("medistock_theme") === "dark";

themeToggle.addEventListener("change", () => {
    const theme = themeToggle.checked ? "dark" : "light";
    localStorage.setItem("medistock_theme", theme);
    document.documentElement.dataset.theme = theme;
    settingsStatus.textContent = `${theme === "dark" ? "Dark" : "Light"} theme applied.`;
});

async function initializeBillingSettings() {
    try {
        const user = await getCurrentUser();
        if (user.role !== "owner") return;

        storeSettingsCard.hidden = false;
        billingSettingsCard.hidden = false;
        const [billingSettings, storeSettings] = await Promise.all([
            apiRequest("/api/v1/settings"),
            apiRequest("/api/v1/settings/store")
        ]);
        defaultTaxPercentage.value = String(billingSettings.default_tax_percentage);
        invoicePrefix.value = billingSettings.invoice_prefix;
        for (const [key, field] of Object.entries(storeFields)) {
            field.value = storeSettings[key] || "";
        }
    } catch (error) {
        billingSettingsStatus.textContent = error.message || "Unable to load settings.";
        billingSettingsStatus.classList.add("is-error");
        storeSettingsStatus.textContent = error.message || "Unable to load settings.";
        storeSettingsStatus.classList.add("is-error");
    }
}

billingSettingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    billingSettingsStatus.textContent = "Saving…";
    billingSettingsStatus.classList.remove("is-error");

    try {
        const settings = await apiRequest("/api/v1/settings", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                default_tax_percentage: Number(defaultTaxPercentage.value),
                invoice_prefix: invoicePrefix.value.trim().toUpperCase()
            })
        });
        defaultTaxPercentage.value = String(settings.default_tax_percentage);
        invoicePrefix.value = settings.invoice_prefix;
        billingSettingsStatus.textContent = "Billing defaults saved.";
    } catch (error) {
        billingSettingsStatus.textContent = error.message;
        billingSettingsStatus.classList.add("is-error");
    }
});

storeSettingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    storeSettingsStatus.textContent = "Saving…";
    storeSettingsStatus.classList.remove("is-error");
    storeSettingsSaveButton.disabled = true;

    try {
        const payload = Object.fromEntries(
            Object.entries(storeFields).map(([key, field]) => [key, field.value.trim()])
        );
        const saved = await apiRequest("/api/v1/settings/store", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        for (const [key, field] of Object.entries(storeFields)) {
            field.value = saved[key] || "";
        }
        storeSettingsStatus.textContent = "Store details saved.";
    } catch (error) {
        storeSettingsStatus.textContent = error.message || "Unable to save store details.";
        storeSettingsStatus.classList.add("is-error");
    } finally {
        storeSettingsSaveButton.disabled = false;
    }
});

initializeBillingSettings();
