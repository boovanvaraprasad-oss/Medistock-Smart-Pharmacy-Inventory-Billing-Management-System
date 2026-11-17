// Activity Log: System Events & Customer Inquiries
const auditRows = document.getElementById("auditRows");
const auditPageSize = 25;
let auditPage = 1;
let auditTotal = 0;

// Tab elements
const tabSystemEvents = document.getElementById("tabSystemEvents");
const tabInquiries = document.getElementById("tabInquiries");
const systemEventsPanel = document.getElementById("systemEventsPanel");
const inquiriesPanel = document.getElementById("inquiriesPanel");
const inquiryTabBadge = document.getElementById("inquiryTabBadge");

// Customer inquiries elements
const inquiryCountBadge = document.getElementById("inquiryCountBadge");
const inquiriesList = document.getElementById("inquiriesList");
const inquirySearchInput = document.getElementById("inquirySearchInput");
const inquiryActionStatus = document.getElementById("inquiryActionStatus");
const filterButtons = document.querySelectorAll(".inquiry-filter-btn");

let allInquiries = [];
let currentInquiryFilter = "all";

const auditActionLabels = {
    BILL_COMPLETE: "Bill completed", BILL_RETURN: "Bill returned",
    STOCK_ADJUSTMENT: "Stock adjusted", STOCK_REDUCE: "Stock reduced", STOCK_BATCH_CREATE: "Stock batch created",
    PURCHASE_ORDER_CREATE: "Purchase order created", PURCHASE_ORDER_UPDATE: "Purchase order changed",
    PURCHASE_ORDER_ITEM_ADD: "Purchase item added", PURCHASE_ORDER_ITEM_UPDATE: "Purchase item changed",
    PURCHASE_ORDER_RECEIVE: "Purchase order received", USER_CREATE: "Staff account created",
    USER_UPDATE: "Staff account changed", USER_DELETE: "Staff account deleted",
    MASTER_DATA_DELETE: "Master data deleted"
};

const auditEntityLabels = {
    bills: "Bill", medicines: "Medicine", stock_batches: "Stock batch",
    purchase_orders: "Purchase order", users: "Staff account",
    categories: "Category", manufacturers: "Manufacturer", units: "Unit", suppliers: "Supplier"
};

const inquirySubjectLabels = {
    demo: "Live System Demo",
    onboarding: "New Pharmacy Onboarding",
    technical: "Technical Support",
    general: "General Inquiry"
};

const inquiryStatusLabels = {
    new: "New",
    in_progress: "In Progress",
    resolved: "Resolved",
    archived: "Archived"
};

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function appendAuditCell(row, text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) cell.className = className;
    row.append(cell);
    return cell;
}

function auditTimestamp(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }).format(date);
}

function auditDetailsText(details) {
    return Object.entries(details || {}).map(([key, value]) => {
        const label = key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
        const shownValue = typeof value === "object" && value !== null ? JSON.stringify(value) : String(value);
        return `${label}: ${shownValue}`;
    }).join(" · ") || "—";
}

function renderAuditRows(items) {
    auditRows.replaceChildren();
    document.getElementById("auditEmpty").hidden = items.length > 0;
    for (const entry of items) {
        const row = document.createElement("tr");
        appendAuditCell(row, auditTimestamp(entry.created_at));
        appendAuditCell(row, auditActionLabels[entry.action] || entry.action, "audit-action");
        const entityType = auditEntityLabels[entry.entity_type] || entry.entity_type || "Record";
        const recordRef = entry.entity_label && entry.entity_label !== entry.entity_id
            ? entry.entity_label
            : entry.entity_id
                ? `#${entry.entity_id.slice(-6)}`
                : "—";
        const recordCell = appendAuditCell(row, `${entityType} · ${recordRef}`);
        if (entry.entity_id) recordCell.title = `Record ID: ${entry.entity_id}`;
        const actor = entry.actor_name || entry.actor_email || "Unknown user";
        const role = (entry.actor_role || "unknown").replaceAll("_", " ");
        appendAuditCell(row, `${actor} · ${role}`);
        appendAuditCell(row, auditDetailsText(entry.details), "audit-details");
        auditRows.append(row);
    }
}

async function loadAuditTrail() {
    const status = document.getElementById("auditStatus");
    const error = document.getElementById("auditError");
    status.hidden = false;
    status.textContent = "Loading audit events…";
    error.hidden = true;
    document.getElementById("auditRefresh").disabled = true;
    try {
        const params = new URLSearchParams({ page: String(auditPage), limit: String(auditPageSize) });
        const q = document.getElementById("auditSearch").value.trim();
        const action = document.getElementById("auditAction").value;
        const entity = document.getElementById("auditEntity").value;
        if (q) params.set("q", q);
        if (action) params.set("action", action);
        if (entity) params.set("entity_type", entity);
        const data = await apiRequest(`/api/v1/audit-logs?${params}`);
        auditTotal = data.total;
        renderAuditRows(data.items);
        document.getElementById("auditCount").textContent = new Intl.NumberFormat("en-IN").format(auditTotal);
        const pageCount = Math.max(1, Math.ceil(auditTotal / auditPageSize));
        document.getElementById("auditPageLabel").textContent = `Page ${auditPage} of ${pageCount}`;
        document.getElementById("auditPrevious").disabled = auditPage <= 1;
        document.getElementById("auditNext").disabled = auditPage >= pageCount;
        status.hidden = true;
    } catch (caught) {
        status.hidden = true;
        error.textContent = caught.message || "Unable to load the activity log.";
        error.hidden = false;
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    } finally {
        document.getElementById("auditRefresh").disabled = false;
    }
}

// Customer Inquiries Logic
function renderInquiries() {
    if (!inquiriesList) return;

    const searchTerm = (inquirySearchInput?.value || "").toLowerCase().trim();

    const filtered = allInquiries.filter((inq) => {
        const matchesFilter = currentInquiryFilter === "all" || inq.status === currentInquiryFilter;
        if (!matchesFilter) return false;
        if (!searchTerm) return true;

        const haystack = [
            inq.name,
            inq.pharmacy,
            inq.email,
            inq.phone,
            inq.message,
            inquirySubjectLabels[inq.subject] || inq.subject
        ].filter(Boolean).join(" ").toLowerCase();

        return haystack.includes(searchTerm);
    });

    const newCount = allInquiries.filter((inq) => inq.status === "new").length;
    if (inquiryCountBadge) {
        inquiryCountBadge.textContent = `${allInquiries.length} total · ${newCount} new`;
    }

    if (inquiryTabBadge) {
        if (newCount > 0) {
            inquiryTabBadge.textContent = String(newCount);
            inquiryTabBadge.hidden = false;
        } else {
            inquiryTabBadge.hidden = true;
        }
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
        const displaySubject = inquirySubjectLabels[inq.subject] || inq.subject || "General Inquiry";
        const displayStatus = inquiryStatusLabels[inq.status] || inq.status;

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
                        inquiryActionStatus.textContent = `Status updated to ${inquiryStatusLabels[targetStatus] || targetStatus}.`;
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

async function loadInquiries() {
    try {
        allInquiries = await apiRequest("/api/v1/inquiries");
        renderInquiries();
    } catch (err) {
        if (inquiriesList) {
            inquiriesList.innerHTML = `<p class="inquiry-empty is-error">${err.message || "Unable to load customer inquiries."}</p>`;
        }
    }
}

// Tab Switching
function switchTab(tabKey) {
    if (tabKey === "inquiries") {
        tabInquiries.classList.add("is-active");
        tabInquiries.setAttribute("aria-selected", "true");
        tabSystemEvents.classList.remove("is-active");
        tabSystemEvents.setAttribute("aria-selected", "false");
        inquiriesPanel.hidden = false;
        systemEventsPanel.hidden = true;
        history.replaceState(null, "", "#inquiries");
    } else {
        tabSystemEvents.classList.add("is-active");
        tabSystemEvents.setAttribute("aria-selected", "true");
        tabInquiries.classList.remove("is-active");
        tabInquiries.setAttribute("aria-selected", "false");
        systemEventsPanel.hidden = false;
        inquiriesPanel.hidden = true;
        history.replaceState(null, "", "#system-events");
    }
}

tabSystemEvents.addEventListener("click", () => switchTab("systemEvents"));
tabInquiries.addEventListener("click", () => switchTab("inquiries"));

// Filter tabs for inquiries
filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        filterButtons.forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        currentInquiryFilter = btn.dataset.filter || "all";
        renderInquiries();
    });
});

if (inquirySearchInput) {
    inquirySearchInput.addEventListener("input", renderInquiries);
}

// Audit trail event listeners
document.getElementById("auditFilters").addEventListener("submit", (event) => {
    event.preventDefault();
    auditPage = 1;
    loadAuditTrail();
});

document.getElementById("auditRefresh").addEventListener("click", async () => {
    await Promise.all([loadAuditTrail(), loadInquiries()]);
});

document.getElementById("auditPrevious").addEventListener("click", () => {
    if (auditPage > 1) {
        auditPage -= 1;
        loadAuditTrail();
    }
});

document.getElementById("auditNext").addEventListener("click", () => {
    if (auditPage * auditPageSize < auditTotal) {
        auditPage += 1;
        loadAuditTrail();
    }
});

// Main Initializer
async function initializeActivityLog() {
    try {
        const user = await getCurrentUser();
        if (!["owner", "compliance_officer", "store_manager"].includes(user.role)) {
            window.location.replace(getDashboardForRole(user.role));
            return;
        }

        // Check if opened with #inquiries in URL
        if (window.location.hash === "#inquiries") {
            switchTab("inquiries");
        }

        await Promise.all([loadAuditTrail(), loadInquiries()]);
    } catch (caught) {
        const error = document.getElementById("auditError");
        if (error) {
            error.textContent = caught.message || "Authentication error.";
            error.hidden = false;
        }
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    }
}

initializeActivityLog();
