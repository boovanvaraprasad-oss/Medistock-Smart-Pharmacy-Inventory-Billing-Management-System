(() => {
    const navigationItems = [
        { label: "Overview", href: "dashboard.html", icon: "⌂", permissions: [] },
        { label: "Staff & Users", href: "users.html", icon: "♙", permissions: ["user:read", "user:write"] },
        { label: "Medicines", href: "medicines.html", icon: "✚", permissions: ["medicine:read", "medicine:write"] },
        { label: "Stock Batches", href: "batches.html", icon: "▦", permissions: ["stock:read"] },
        { label: "Categories", href: "categories.html", icon: "▦", permissions: ["medicine:read", "medicine:write"] },
        { label: "Manufacturers", href: "manufacturers.html", icon: "▤", permissions: ["medicine:read", "medicine:write"] },
        { label: "Units", href: "units.html", icon: "◫", permissions: ["medicine:read", "medicine:write"] },
        { label: "Suppliers", href: "suppliers.html", icon: "♧", permissions: ["supplier:read", "supplier:write"] },
        { label: "Purchase Orders", href: "purchase_orders.html", icon: "▣", permissions: ["purchase:read", "purchase:write"] },
        { label: "Billing", href: "billing.html", icon: "▤", permissions: ["bill:read", "bill:create"] },
        { label: "Login History", href: "login_history.html", icon: "◷", permissions: [], roles: ["owner", "store_manager"] }
    ];

    function addSidebar(currentUser) {
        const overviewPage = getDashboardForRole(currentUser.role);
        const sidebar = document.createElement("aside");
        sidebar.className = "app-sidebar";

        const brand = document.createElement("a");
        brand.className = "app-sidebar-brand";
        brand.href = overviewPage;
        brand.setAttribute("aria-label", "MediStock overview");

        const mark = document.createElement("span");
        mark.className = "app-sidebar-mark";
        mark.setAttribute("aria-hidden", "true");
        mark.textContent = "✚";

        const brandCopy = document.createElement("span");
        brandCopy.className = "app-sidebar-brand-copy";
        const brandName = document.createElement("strong");
        brandName.textContent = "MediStock";
        const brandDescription = document.createElement("small");
        brandDescription.textContent = "Pharmacy inventory";
        brandCopy.append(brandName, brandDescription);

        const toggle = document.createElement("button");
        toggle.className = "app-sidebar-toggle";
        toggle.type = "button";
        toggle.setAttribute("aria-label", "Open navigation menu");
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = "☰";
        brand.append(mark, brandCopy, toggle);

        const menu = document.createElement("div");
        menu.className = "app-sidebar-menu";

        const nav = document.createElement("nav");
        nav.className = "app-side-nav";
        nav.setAttribute("aria-label", "Main navigation");
        const currentFile = window.location.pathname.split("/").pop() || "index.html";
        const permissions = currentUser.permissions || [];

        for (const item of navigationItems) {
            if (item.roles && !item.roles.includes(currentUser.role)) {
                continue;
            }
            if (item.permissions.length && !item.permissions.some((permission) => permissions.includes(permission))) {
                continue;
            }

            const link = document.createElement("a");
            link.className = "app-side-link";
            const pageHref = item.label === "Overview" ? overviewPage : item.href;
            link.href = pageHref;
            if (currentFile === pageHref) link.setAttribute("aria-current", "page");

            const icon = document.createElement("span");
            icon.className = "app-side-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = item.icon;
            const label = document.createElement("span");
            label.textContent = item.label;
            link.append(icon, label);
            nav.append(link);
        }

        const footer = document.createElement("div");
        footer.className = "app-sidebar-footer";
        const avatar = document.createElement("span");
        avatar.className = "app-sidebar-avatar";
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = (currentUser.name || currentUser.email || "U").trim().charAt(0).toUpperCase();

        const userInfo = document.createElement("span");
        userInfo.className = "app-sidebar-user";
        const userName = document.createElement("strong");
        userName.textContent = currentUser.name || currentUser.email || "User";
        const role = document.createElement("small");
        role.textContent = (currentUser.role || "Staff")
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());
        userInfo.append(userName, role);

        const logout = document.createElement("button");
        logout.className = "app-sidebar-logout";
        logout.type = "button";
        logout.setAttribute("aria-label", "Log out");
        logout.title = "Log out";
        logout.innerHTML = `
            <span class="app-sidebar-logout-sign" aria-hidden="true">
                <svg viewBox="0 0 512 512" focusable="false">
                    <path d="M377.9 105.9L500.7 228.7c7.2 7.2 11.3 17.1 11.3 27.3s-4.1 20.1-11.3 27.3L377.9 406.1c-6.4 6.4-15 9.9-24 9.9c-18.7 0-33.9-15.2-33.9-33.9l0-62.1-128 0c-17.7 0-32-14.3-32-32l0-64c0-17.7 14.3-32 32-32l128 0 0-62.1c0-18.7 15.2-33.9 33.9-33.9c9 0 17.6 3.6 24 9.9zM160 96L96 96c-17.7 0-32 14.3-32 32l0 256c0 17.7 14.3 32 32 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-64 0c-53 0-96-43-96-96L0 128C0 75 43 32 96 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32z"></path>
                </svg>
            </span>
            <span class="app-sidebar-logout-text">Logout</span>
        `;
        logout.addEventListener("click", async () => {
            logout.disabled = true;
            try {
                await logoutUser();
            } catch {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                sessionStorage.removeItem("medistock_current_user");
            } finally {
                window.location.href = "/";
            }
        });

        userInfo.append(logout);
        footer.append(avatar, userInfo);
        menu.append(nav, footer);
        sidebar.append(brand, menu);

        toggle.addEventListener("click", () => {
            const open = sidebar.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(open));
            toggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
            toggle.textContent = open ? "×" : "☰";
        });

        document.body.classList.add("has-app-sidebar");
        document.body.insertBefore(sidebar, document.body.firstChild);
    }

    async function initializeAppShell() {
        if (!localStorage.getItem("access_token")) {
            sessionStorage.removeItem("medistock_current_user");
            window.location.href = "/";
            return;
        }

        const cachedUser = getCachedCurrentUser();
        if (cachedUser) {
            addSidebar(cachedUser);
            window.addEventListener("medistock:current-user", (event) => {
                const sidebar = document.querySelector(".app-sidebar");
                if (!sidebar) return;
                sidebar.remove();
                document.body.classList.remove("has-app-sidebar");
                addSidebar(event.detail);
            });
            return;
        }

        try {
            const currentUser = await getCurrentUser();
            addSidebar(currentUser);
        } catch {
            window.location.href = "/";
        }
    }

    function getCachedCurrentUser() {
        try {
            return JSON.parse(sessionStorage.getItem("medistock_current_user") || "null");
        } catch {
            sessionStorage.removeItem("medistock_current_user");
            return null;
        }
    }

    initializeAppShell();
})();
