const statusMessage = document.getElementById("statusMessage");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const userRows = document.getElementById("userRows");
const listDescription = document.getElementById("listDescription");
const createSection = document.getElementById("createSection");
const createForm = document.getElementById("createForm");
const createButton = document.getElementById("createButton");
const refreshButton = document.getElementById("refreshButton");
const newRole = document.getElementById("newRole");

const STAFF_ROLES = [
    ["pharmacist", "Pharmacist"],
    ["inventory_executive", "Inventory executive"],
    ["purchase_executive", "Purchase executive"],
    ["store_manager", "Store manager"],
    ["compliance_officer", "Compliance officer"]
];

let currentUser = null;
let permissions = [];
let staffUsers = [];

function showMessage(element, message) {
    element.textContent = message;
    element.hidden = !message;
}

function roleLabel(role) {
    const match = STAFF_ROLES.find(([value]) => value === role);
    return match ? match[1] : role.replaceAll("_", " ");
}

function makeButton(label, className, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
}

function makeRoleSelect(selectedRole) {
    const select = document.createElement("select");
    select.className = "role-select";
    select.setAttribute("aria-label", "Staff role");

    for (const [value, label] of STAFF_ROLES) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        option.selected = value === selectedRole;
        select.appendChild(option);
    }

    return select;
}

async function updateUser(user, changes, successText) {
    showMessage(errorMessage, "");
    showMessage(successMessage, "");

    try {
        await apiRequest(`/api/v1/users/${encodeURIComponent(user.id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(changes)
        });
        showMessage(successMessage, successText);
        await loadUsers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    }
}

function renderUsers() {
    userRows.replaceChildren();

    if (staffUsers.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.textContent = "No staff accounts found.";
        row.appendChild(cell);
        userRows.appendChild(row);
        return;
    }

    for (const user of staffUsers) {
        const row = document.createElement("tr");
        const emailCell = document.createElement("td");
        emailCell.textContent = user.email;
        row.appendChild(emailCell);

        const roleCell = document.createElement("td");
        roleCell.textContent = roleLabel(user.role);
        row.appendChild(roleCell);

        const statusCell = document.createElement("td");
        const statusPill = document.createElement("span");
        statusPill.className = `status-pill ${user.is_active ? "status-active" : "status-inactive"}`;
        statusPill.textContent = user.is_active ? "Active" : "Inactive";
        statusCell.appendChild(statusPill);
        row.appendChild(statusCell);

        const actionsCell = document.createElement("td");
        actionsCell.className = "actions-cell";
        const actions = document.createElement("div");
        actions.className = "row-actions";

        if (permissions.includes("user:write") && user.role !== "owner") {
            const roleSelect = makeRoleSelect(user.role);
            const saveRoleButton = makeButton(
                "Save changes",
                "button button-secondary button-small",
                () => updateUser(user, { role: roleSelect.value }, "Staff role updated.")
            );
            saveRoleButton.classList.add("save-changes-button");
            saveRoleButton.disabled = true;
            saveRoleButton.title = "Choose a different role to enable Save changes.";

            roleSelect.addEventListener("change", () => {
                const hasChanged = roleSelect.value !== user.role;
                saveRoleButton.disabled = !hasChanged;
                saveRoleButton.title = hasChanged
                    ? "Save the selected role."
                    : "Choose a different role to enable Save changes.";
                saveRoleButton.classList.toggle("button-primary", hasChanged);
                saveRoleButton.classList.toggle("button-secondary", !hasChanged);
            });

            const statusButton = makeButton(
                user.is_active ? "Deactivate" : "Activate",
                "button button-secondary button-small",
                () => updateUser(
                    user,
                    { is_active: !user.is_active },
                    user.is_active ? "Staff account deactivated." : "Staff account activated."
                )
            );
            if (user.id === currentUser.id) {
                statusButton.disabled = true;
                statusButton.title = "You cannot deactivate your own account.";
            }
            actions.append(roleSelect, statusButton, saveRoleButton);
        }

        if (
            permissions.includes("user:delete")
            && user.id !== currentUser.id
            && user.role !== "owner"
            && !user.is_active
        ) {
            const deleteButton = makeButton(
                "Delete permanently",
                "button button-danger button-small",
                async () => {
                    const confirmed = window.confirm(
                        `Permanently delete ${user.email}? This cannot be undone. Accounts referenced in audit history cannot be deleted.`
                    );
                    if (!confirmed) return;

                    showMessage(errorMessage, "");
                    showMessage(successMessage, "");
                    try {
                        const result = await apiRequest(
                            `/api/v1/users/${encodeURIComponent(user.id)}`,
                            { method: "DELETE" }
                        );
                        showMessage(successMessage, result.message || "Staff account deleted.");
                        await loadUsers();
                    } catch (error) {
                        showMessage(errorMessage, error.message);
                    }
                }
            );
            actions.appendChild(deleteButton);
        }

        if (!actions.childElementCount) {
            actions.textContent = user.role === "owner" ? "Protected owner account" : "View only";
        }

        actionsCell.appendChild(actions);
        row.appendChild(actionsCell);
        userRows.appendChild(row);
    }
}

async function loadUsers() {
    showMessage(errorMessage, "");
    statusMessage.textContent = "Loading staff accounts…";
    statusMessage.hidden = false;
    refreshButton.disabled = true;

    try {
        staffUsers = await apiRequest("/api/v1/users");
        renderUsers();
        listDescription.textContent = `${staffUsers.length} account${staffUsers.length === 1 ? "" : "s"}`;
        statusMessage.hidden = true;
    } catch (error) {
        listDescription.textContent = "Could not load staff accounts.";
        showMessage(statusMessage, "");
        showMessage(errorMessage, error.message);
        if (error.message.includes("Permission denied")) {
            errorMessage.textContent = "Your role can’t view staff accounts.";
        }
    } finally {
        refreshButton.disabled = false;
    }
}

async function initializeUsersPage() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }

    try {
        currentUser = await apiRequest("/api/v1/auth/me");
        permissions = currentUser.permissions || [];

        if (permissions.includes("user:write")) {
            createSection.hidden = false;
            for (const [value, label] of STAFF_ROLES) {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = label;
                newRole.appendChild(option);
            }
        }

        if (!permissions.includes("user:read")) {
            showMessage(errorMessage, "Your role can’t view staff accounts.");
            listDescription.textContent = "Access restricted.";
            return;
        }

        await loadUsers();
    } catch (error) {
        showMessage(errorMessage, error.message);
        if (!localStorage.getItem("access_token")) window.location.href = "/";
    }
}

createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(errorMessage, "");
    showMessage(successMessage, "");
    createButton.disabled = true;

    const email = document.getElementById("newEmail").value.trim();
    const password = document.getElementById("newPassword").value;

    try {
        const created = await apiRequest("/api/v1/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, role: newRole.value })
        });
        createForm.reset();
        showMessage(successMessage, `Created ${created.email}.`);
        await loadUsers();
    } catch (error) {
        showMessage(errorMessage, error.message);
    } finally {
        createButton.disabled = false;
    }
});

refreshButton.addEventListener("click", loadUsers);
initializeUsersPage();
