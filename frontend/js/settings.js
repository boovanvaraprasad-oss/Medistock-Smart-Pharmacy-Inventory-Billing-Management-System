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
        if (user.role === "owner" || user.role === "store_manager") {
            await initializeSMTPSettings(user);
        }
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

// SMTP Mailer Management & Live Test
const smtpSettingsCard = document.getElementById("smtpSettingsCard");
const smtpConfiguredBadge = document.getElementById("smtpConfiguredBadge");
const smtpHostVal = document.getElementById("smtpHostVal");
const smtpFromVal = document.getElementById("smtpFromVal");
const smtpAdminVal = document.getElementById("smtpAdminVal");
const smtpTestForm = document.getElementById("smtpTestForm");
const smtpTestEmail = document.getElementById("smtpTestEmail");
const smtpTestButton = document.getElementById("smtpTestButton");
const smtpTestStatus = document.getElementById("smtpTestStatus");

async function initializeSMTPSettings(user) {
    if (user.role !== "owner" && user.role !== "store_manager") return;

    if (smtpSettingsCard) smtpSettingsCard.hidden = false;

    // Load SMTP Status
    try {
        const smtpStatus = await apiRequest("/api/v1/inquiries/smtp-status");
        if (smtpConfiguredBadge) {
            if (smtpStatus.configured) {
                smtpConfiguredBadge.textContent = "✓ Configured";
                smtpConfiguredBadge.className = "smtp-badge is-ready";
            } else {
                smtpConfiguredBadge.textContent = "⚠ Not Configured in .env";
                smtpConfiguredBadge.className = "smtp-badge is-missing";
            }
        }
        if (smtpHostVal) smtpHostVal.textContent = `${smtpStatus.host}:${smtpStatus.port}`;
        if (smtpFromVal) smtpFromVal.textContent = smtpStatus.from_email || "—";
        if (smtpAdminVal) smtpAdminVal.textContent = smtpStatus.admin_email || "—";
        if (smtpTestEmail && !smtpTestEmail.value) {
            smtpTestEmail.value = user.email || smtpStatus.admin_email || "";
        }
    } catch (err) {
        if (smtpTestStatus) {
            smtpTestStatus.textContent = "Could not check SMTP status: " + err.message;
            smtpTestStatus.classList.add("is-error");
        }
    }
}

if (smtpTestForm) {
    smtpTestForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const targetEmail = smtpTestEmail.value.trim();
        if (!targetEmail) return;

        smtpTestButton.disabled = true;
        smtpTestButton.textContent = "Connecting to SMTP…";
        smtpTestStatus.textContent = "Initiating connection to SMTP server and dispatching verification email…";
        smtpTestStatus.classList.remove("is-error");

        try {
            const res = await apiRequest("/api/v1/inquiries/test-smtp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target_email: targetEmail })
            });
            smtpTestStatus.textContent = `✓ ${res.message || "Test email delivered successfully! Please check your inbox."}`;
            smtpTestStatus.classList.remove("is-error");
        } catch (err) {
            smtpTestStatus.textContent = `⚠ ${err.message || "SMTP test failed. Verify host, port, and App Password in backend/.env."}`;
            smtpTestStatus.classList.add("is-error");
        } finally {
            smtpTestButton.disabled = false;
            smtpTestButton.textContent = "Send test email";
        }
    });
}

initializeBillingSettings();
