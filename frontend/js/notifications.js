const notificationList = document.getElementById("notificationList");
const notificationCount = document.getElementById("notificationCount");
const notificationEmpty = document.getElementById("notificationEmpty");
const notificationError = document.getElementById("notificationError");
const notificationFilter = document.getElementById("notificationFilter");
const markAllReadButton = document.getElementById("markAllReadButton");
let notificationState = { items: [], unread_count: 0, total_count: 0 };

function renderNotifications() {
    notificationList.replaceChildren();
    const unreadOnly = notificationFilter.value === "unread";
    const items = notificationState.items.filter((item) => !unreadOnly || !item.is_read);
    notificationCount.textContent = `${notificationState.unread_count} unread · ${notificationState.total_count} active`;
    markAllReadButton.disabled = notificationState.unread_count === 0;
    notificationEmpty.hidden = items.length > 0;
    notificationEmpty.textContent = unreadOnly
        ? "There are no unread notifications."
        : "You’re all caught up. There are no active notifications.";

    items.forEach((item) => {
        const card = document.createElement("article");
        card.className = `notification-card priority-${item.priority}${item.is_read ? " is-read" : " is-unread"}`;
        const icon = document.createElement("span");
        icon.className = "notification-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = item.priority === "critical" ? "!" : item.priority === "warning" ? "◷" : "▣";

        const body = document.createElement("div");
        body.className = "notification-copy";
        const title = document.createElement("h2");
        title.textContent = item.title;
        const message = document.createElement("p");
        message.textContent = item.message;
        body.append(title, message);
        if (item.sku || item.expiry_date) {
            const detail = document.createElement("small");
            detail.textContent = [item.sku && `SKU ${item.sku}`, item.expiry_date && `Expiry ${new Date(`${item.expiry_date}T00:00:00`).toLocaleDateString("en-IN")}`].filter(Boolean).join(" · ");
            body.append(detail);
        }

        const actions = document.createElement("div");
        actions.className = "notification-actions";
        const open = document.createElement("a");
        open.href = item.href || "dashboard.html";
        open.className = "notification-open-link";
        open.textContent = "View";
        actions.append(open);

        if (!item.is_read) {
            const readButton = document.createElement("button");
            readButton.type = "button";
            readButton.textContent = "Mark read";
            readButton.addEventListener("click", () => markRead(item.id));
            actions.append(readButton);
        }
        card.append(icon, body, actions);
        notificationList.append(card);
    });
}

async function loadNotifications() {
    notificationError.hidden = true;
    try {
        notificationState = await apiRequest("/api/v1/notifications");
        renderNotifications();
    } catch (error) {
        notificationError.textContent = error.message;
        notificationError.hidden = false;
        notificationCount.textContent = "Notifications could not be loaded.";
    }
}

async function markRead(notificationId) {
    try {
        notificationState = await apiRequest("/api/v1/notifications/read", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ notification_id: notificationId })
        });
        renderNotifications();
    } catch (error) {
        notificationError.textContent = error.message;
        notificationError.hidden = false;
    }
}

notificationFilter.addEventListener("change", renderNotifications);
markAllReadButton.addEventListener("click", async () => {
    markAllReadButton.disabled = true;
    try {
        notificationState = await apiRequest("/api/v1/notifications/read-all", { method: "POST" });
        renderNotifications();
    } catch (error) {
        notificationError.textContent = error.message;
        notificationError.hidden = false;
        markAllReadButton.disabled = false;
    }
});

loadNotifications();
