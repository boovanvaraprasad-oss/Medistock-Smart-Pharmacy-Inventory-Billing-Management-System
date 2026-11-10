const themeToggle = document.getElementById("themeToggle");
const settingsStatus = document.getElementById("settingsStatus");
const billingSettingsCard = document.getElementById("billingSettingsCard");
const billingSettingsForm = document.getElementById("billingSettingsForm");
const defaultTaxPercentage = document.getElementById("defaultTaxPercentage");
const invoicePrefix = document.getElementById("invoicePrefix");
const billingSettingsStatus = document.getElementById("billingSettingsStatus");

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

        billingSettingsCard.hidden = false;
        const settings = await apiRequest("/api/v1/settings");
        defaultTaxPercentage.value = String(settings.default_tax_percentage);
        invoicePrefix.value = settings.invoice_prefix;
    } catch (error) {
        billingSettingsStatus.textContent = error.message;
        billingSettingsStatus.classList.add("is-error");
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

initializeBillingSettings();
