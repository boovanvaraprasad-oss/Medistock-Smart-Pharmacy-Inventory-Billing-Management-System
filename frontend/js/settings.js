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
            await initializeSMTPAndInquiries(user);
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

// Customer Inquiries & Leads Management
const inquiriesCard = document.getElementById("inquiriesCard");
const inquiryCountBadge = document.getElementById("inquiryCountBadge");
const inquiriesList = document.getElementById("inquiriesList");
const inquirySearchInput = document.getElementById("inquirySearchInput");
const inquiryActionStatus = document.getElementById("inquiryActionStatus");
const filterButtons = document.querySelectorAll(".inquiry-filter-btn");

let allInquiries = [];
let currentFilter = "all";

const subjectLabels = {
    demo: "Live System Demo",
    onboarding: "New Pharmacy Onboarding",
    technical: "Technical Support",
    general: "General Inquiry"
};

const statusLabels = {
    new: "New",
    in_progress: "In Progress",
    resolved: "Resolved",
    archived: "Archived"
};

function renderInquiries() {
    if (!inquiriesList) return;

    const searchTerm = (inquirySearchInput?.value || "").toLowerCase().trim();

    const filtered = allInquiries.filter((inq) => {
        const matchesFilter = currentFilter === "all" || inq.status === currentFilter;
        if (!matchesFilter) return false;
        if (!searchTerm) return true;

        const haystack = [
            inq.name,
            inq.pharmacy,
            inq.email,
            inq.phone,
            inq.message,
            subjectLabels[inq.subject] || inq.subject
        ].filter(Boolean).join(" ").toLowerCase();

        return haystack.includes(searchTerm);
    });

    const newCount = allInquiries.filter((inq) => inq.status === "new").length;
    if (inquiryCountBadge) {
        inquiryCountBadge.textContent = `${allInquiries.length} total · ${newCount} new`;
    }

    if (!filtered.length) {
        inquiriesList.innerHTML = `<p class="inquiry-empty">${allInquiries.length === 0 ? "No customer inquiries received yet." : "No inquiries match the current filter or search."}</p>`;
        return;
    }

    inquiriesList.innerHTML = "";
    filtered.forEach((inq) => {
        const card = document.createElement("article");
        card.className = `inquiry-card status-${inq.status}`;

        const initial = (inq.name || "U").trim().charAt(0).toUpperCase();
        const displaySubject = subjectLabels[inq.subject] || inq.subject || "General Inquiry";
        const displayStatus = statusLabels[inq.status] || inq.status;

        card.innerHTML = `
            <div class="inquiry-card-header">
                <span class="inquiry-avatar" aria-hidden="true">${initial}</span>
                <div class="inquiry-identity">
                    <strong>${escapeHtml(inq.name)}</strong>
                    <small>🏥 ${escapeHtml(inq.pharmacy)}</small>
                </div>
                <div class="inquiry-meta">
                    <span class="inquiry-date">${escapeHtml(inq.created_at || "")}</span>
                    <span class="inquiry-badge badge-${escapeHtml(inq.status)}">${escapeHtml(displayStatus)}</span>
                </div>
            </div>

            <div class="inquiry-details-row">
                <span>✉ <a href="mailto:${encodeURIComponent(inq.email)}" class="inquiry-channel">${escapeHtml(inq.email)}</a></span>
                ${inq.phone ? `<span>📞 <a href="tel:${encodeURIComponent(inq.phone)}" class="inquiry-channel">${escapeHtml(inq.phone)}</a></span>` : `<span style="color: #839b9e;">No phone</span>`}
                <span class="inquiry-tag">${escapeHtml(displaySubject)}</span>
            </div>

            <div class="inquiry-message">${escapeHtml(inq.message)}</div>

            <div class="inquiry-actions-row">
                <a href="mailto:${encodeURIComponent(inq.email)}?subject=Re:%20${encodeURIComponent(displaySubject)}%20-%20MediStock%20Pharmacy" class="inquiry-action-btn btn-primary-action">Reply via Email &rarr;</a>
                ${inq.status === "new" ? `<button type="button" class="inquiry-action-btn" data-action="in_progress" data-id="${inq.id}">Start Review</button>` : ""}
                ${inq.status !== "resolved" ? `<button type="button" class="inquiry-action-btn" data-action="resolved" data-id="${inq.id}">✓ Mark Resolved</button>` : ""}
                ${inq.status === "resolved" ? `<button type="button" class="inquiry-action-btn" data-action="new" data-id="${inq.id}">↺ Reopen</button>` : ""}
            </div>
        `;

        card.querySelectorAll("button[data-action]").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const targetStatus = btn.dataset.action;
                const inquiryId = btn.dataset.id;
                btn.disabled = true;
                try {
                    await apiRequest(`/api/v1/inquiries/${inquiryId}/status`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ status: targetStatus })
                    });
                    const found = allInquiries.find((item) => item.id === inquiryId);
                    if (found) found.status = targetStatus;
                    renderInquiries();
                    if (inquiryActionStatus) {
                        inquiryActionStatus.textContent = `Status updated to ${statusLabels[targetStatus] || targetStatus}.`;
                        inquiryActionStatus.classList.remove("is-error");
                        setTimeout(() => { if (inquiryActionStatus) inquiryActionStatus.textContent = ""; }, 3000);
                    }
                } catch (err) {
                    if (inquiryActionStatus) {
                        inquiryActionStatus.textContent = err.message || "Failed to update status.";
                        inquiryActionStatus.classList.add("is-error");
                    }
                } finally {
                    btn.disabled = false;
                }
            });
        });

        inquiriesList.appendChild(card);
    });
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        filterButtons.forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        currentFilter = btn.dataset.filter || "all";
        renderInquiries();
    });
});

if (inquirySearchInput) {
    inquirySearchInput.addEventListener("input", renderInquiries);
}

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

async function initializeSMTPAndInquiries(user) {
    if (user.role !== "owner" && user.role !== "store_manager") return;

    if (inquiriesCard) inquiriesCard.hidden = false;
    if (smtpSettingsCard) smtpSettingsCard.hidden = false;

    // Load inquiries
    try {
        allInquiries = await apiRequest("/api/v1/inquiries");
        renderInquiries();
    } catch (err) {
        if (inquiriesList) {
            inquiriesList.innerHTML = `<p class="inquiry-empty is-error">${err.message || "Unable to load customer inquiries."}</p>`;
        }
    }

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
