(() => {
    const navigationItems = [
        { label: "Overview", href: "dashboard.html", icon: "⌂", permissions: [] },
        { label: "Staff & Users", href: "users.html", icon: "♙", permissions: ["user:read", "user:write"] },
        { label: "Medicines", href: "medicines.html", icon: "✚", permissions: ["medicine:read", "medicine:write"] },
        { label: "Categories", href: "categories.html", icon: "▦", permissions: ["medicine:read", "medicine:write"] },
        { label: "Manufacturers", href: "manufacturers.html", icon: "▤", permissions: ["medicine:read", "medicine:write"] },
        { label: "Units", href: "units.html", icon: "◫", permissions: ["medicine:read", "medicine:write"] },
        { label: "Suppliers", href: "suppliers.html", icon: "♧", permissions: ["supplier:read", "supplier:write"] },
        { label: "Purchase Orders", href: "purchase_orders.html", icon: "▣", permissions: ["purchase:read", "purchase:write"] },
        { label: "Billing", href: "billing.html", icon: "▤", permissions: ["bill:read", "bill:create"] }
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
        logout.textContent = "↪";
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

        footer.append(avatar, userInfo, logout);
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
