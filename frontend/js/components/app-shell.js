(() => {
    document.documentElement.dataset.theme = localStorage.getItem("medistock_theme") === "dark" ? "dark" : "light";

    if (!document.querySelector('link[rel="icon"]')) {
        const favicon = document.createElement("link");
        favicon.rel = "icon";
        favicon.type = "image/svg+xml";
        favicon.href = "/assets/medistock-mark.svg";
        document.head.append(favicon);
    }

    const navigationItems = [
        { label: "Dashboard", href: (user) => getDashboardForRole(user.role), icon: "layout-dashboard", permissions: [] },
        { label: "My Profile", href: "profile.html", icon: "user-round", permissions: [] },
        { label: "Staff & Users", href: (user) => (user.permissions?.includes("user:read") || user.role === "owner" ? "users.html" : "login_history.html"), icon: "users", permissions: ["user:read", "user:write", "login_log:read"] },
        { label: "Medicines", href: "medicines.html", icon: "pill", permissions: ["medicine:read", "medicine:write"] },
        { label: "Stock Batches", href: "batches.html", icon: "boxes", permissions: ["stock:read"] },
        { label: "Categories", href: "categories.html", icon: "grid", permissions: ["medicine:read", "medicine:write"] },
        { label: "Manufacturers", href: "manufacturers.html", icon: "factory", permissions: ["medicine:read", "medicine:write"] },
        { label: "Units", href: "units.html", icon: "ruler", permissions: ["medicine:read", "medicine:write"] },
        { label: "Suppliers", href: "suppliers.html", icon: "truck", permissions: ["supplier:read", "supplier:write"] },
        { label: "Purchase Orders", href: "purchase_orders.html", icon: "shopping-cart", permissions: ["purchase:read", "purchase:write"] },
        { label: "Billing", href: "billing.html", icon: "receipt", permissions: ["bill:read", "bill:create"] },
        { label: "Notifications", href: "notifications.html", icon: "bell", permissions: ["stock:read"] },
        { label: "Reports & Analytics", href: "reports.html", icon: "chart-column", permissions: ["report:view"] },
        { label: "Settings", href: "settings.html", icon: "settings", permissions: [] },
        { label: "Audit Trail", href: "audit_trail.html", icon: "audit", permissions: ["audit_log:read"] }
    ];

    function addSidebar(currentUser) {
        const scrollKey = `medistock_sidebar_scroll:${currentUser.id || currentUser._id || currentUser.email || currentUser.role}`;
        const previousNav = document.querySelector(".app-side-nav");
        if (previousNav) {
            sessionStorage.setItem(scrollKey, String(previousNav.scrollTop));
        }

        // The cached user can be refreshed after the shell has already rendered.
        // Clear its previous elements before rebuilding to avoid duplicate profiles.
        document.querySelectorAll(".app-sidebar, .app-header-profile, .app-account-bar, .app-header-notifications").forEach((element) => element.remove());
        const sidebar = document.createElement("aside");
        sidebar.className = "app-sidebar";

        const brand = document.createElement("a");
        brand.className = "app-sidebar-brand";
        brand.href = "home.html";
        brand.setAttribute("aria-label", "MediStock home");

        const mark = document.createElement("img");
        mark.className = "app-sidebar-mark";
        mark.src = "/assets/medistock-mark.svg";
        mark.alt = "";
        mark.setAttribute("aria-hidden", "true");

        const brandCopy = document.createElement("span");
        brandCopy.className = "app-sidebar-brand-copy";
        brandCopy.setAttribute("aria-hidden", "true");
        brandCopy.innerHTML = '<strong><span>Medi</span><span>Stock</span></strong><small>Pharmacy inventory</small>';

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
            const pageHref = typeof item.href === "function" ? item.href(currentUser) : item.href;
            link.href = pageHref;
            const isStaffAndUsersActive = item.label === "Staff & Users" && (currentFile === "users.html" || currentFile === "login_history.html");
            if (currentFile === pageHref || isStaffAndUsersActive) link.setAttribute("aria-current", "page");

            const icon = document.createElement("span");
            icon.className = "app-side-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.append(createNavigationIcon(item.icon));
            const label = document.createElement("span");
            label.textContent = item.label;
            link.append(icon, label);
            nav.append(link);
        }

        const logout = document.createElement("button");
        logout.className = "app-header-profile-logout app-sidebar-logout";
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

        const isDashboardPage = /^(?:dashboard|(?:pharmacist|inventory|purchase|store_manager|compliance)_dashboard)\.html$/.test(currentFile);
        let profile = null;
        if (isDashboardPage) {
            profile = document.createElement("div");
            profile.className = "app-header-profile";
            profile.setAttribute("aria-label", "Signed-in account");

            const profileLink = document.createElement("a");
            profileLink.className = "app-header-profile-link";
            profileLink.href = "profile.html";
            profileLink.title = "View your profile";
            profileLink.setAttribute("aria-label", "View your profile");

            const avatar = document.createElement("span");
            avatar.className = "app-header-profile-avatar";
            avatar.setAttribute("aria-hidden", "true");
            avatar.textContent = (currentUser.full_name || currentUser.name || "U").trim().charAt(0).toUpperCase();

            const userInfo = document.createElement("span");
            userInfo.className = "app-header-profile-details app-header-profile-info";
            const userName = document.createElement("strong");
            userName.className = "app-header-profile-name";
            userName.textContent = currentUser.full_name || currentUser.name || (currentUser.email ? currentUser.email.split("@")[0] : "User");
            const role = document.createElement("small");
            role.className = "app-header-profile-role";
            role.textContent = (currentUser.role || "Staff")
                .replaceAll("_", " ")
                .replace(/\b\w/g, (letter) => letter.toUpperCase());
            userInfo.append(userName, role);

            profileLink.append(avatar, userInfo);
            profile.append(profileLink, logout);
        }

        let notificationsLink = null;
        if (isDashboardPage) {
            notificationsLink = document.createElement("a");
            notificationsLink.className = "app-header-notifications";
            notificationsLink.href = "notifications.html";
            notificationsLink.setAttribute("aria-label", "Notifications");
            const notificationIcon = document.createElement("span");
            notificationIcon.className = "app-header-notification-icon";
            notificationIcon.setAttribute("aria-hidden", "true");
            notificationIcon.append(createNavigationIcon("bell"));
            notificationsLink.append(notificationIcon);
            const notificationBadge = document.createElement("span");
            notificationBadge.className = "app-notification-badge";
            notificationBadge.hidden = true;
            notificationsLink.append(notificationBadge);
        }

        const sidebarFooter = document.createElement("div");
        sidebarFooter.className = "app-sidebar-footer";

        const homeLink = document.createElement("a");
        homeLink.className = "app-sidebar-footer-btn app-sidebar-home-btn";
        homeLink.href = "home.html";
        homeLink.setAttribute("aria-label", "MediStock home");
        if (currentFile === "home.html") {
            homeLink.setAttribute("aria-current", "page");
            homeLink.classList.add("is-active");
        }
        homeLink.innerHTML = `
            <span class="app-sidebar-footer-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" focusable="false">
                    <path d="m3 10 9-7 9 7"></path>
                    <path d="M5 9v12h14V9M9 21v-7h6v7"></path>
                </svg>
            </span>
            <span>Home</span>
        `;

        const sidebarLogout = document.createElement("button");
        sidebarLogout.className = "app-sidebar-footer-btn app-sidebar-logout-btn";
        sidebarLogout.type = "button";
        sidebarLogout.setAttribute("aria-label", "Log out of MediStock");
        sidebarLogout.innerHTML = `
            <span class="app-sidebar-footer-icon" aria-hidden="true">
                <svg viewBox="0 0 512 512" focusable="false">
                    <path d="M377.9 105.9L500.7 228.7c7.2 7.2 11.3 17.1 11.3 27.3s-4.1 20.1-11.3 27.3L377.9 406.1c-6.4 6.4-15 9.9-24 9.9c-18.7 0-33.9-15.2-33.9-33.9l0-62.1-128 0c-17.7 0-32-14.3-32-32l0-64c0-17.7 14.3-32 32-32l128 0 0-62.1c0-18.7 15.2-33.9 33.9-33.9c9 0 17.6 3.6 24 9.9zM160 96L96 96c-17.7 0-32 14.3-32 32l0 256c0 17.7 14.3 32 32 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-64 0c-53 0-96-43-96-96L0 128C0 75 43 32 96 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32z"></path>
                </svg>
            </span>
            <span>Log out</span>
        `;
        sidebarLogout.addEventListener("click", async () => {
            sidebarLogout.disabled = true;
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
        sidebarFooter.append(homeLink, sidebarLogout);
        menu.append(nav, sidebarFooter);
        sidebar.append(brand, menu);

        toggle.addEventListener("click", () => {
            const open = sidebar.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(open));
            toggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
            toggle.textContent = open ? "×" : "☰";
        });

        document.body.classList.add("has-app-sidebar");
        document.body.insertBefore(sidebar, document.body.firstChild);

        const savedScrollTop = Number(sessionStorage.getItem(scrollKey) || 0);
        const restoreSidebarScroll = () => {
            nav.scrollTop = savedScrollTop;
        };
        requestAnimationFrame(restoreSidebarScroll);
        window.addEventListener("pagehide", () => {
            sessionStorage.setItem(scrollKey, String(nav.scrollTop));
        }, { once: true });

        const page = document.querySelector("body > .page");
        const pageHeader = page?.querySelector(".topbar, .page-header, header");
        const pageActions = pageHeader?.querySelector(".topbar-actions");
        if (pageActions) {
            if (notificationsLink) pageActions.append(notificationsLink);
            if (profile) pageActions.append(profile);
        } else if (pageHeader) {
            if (notificationsLink) pageHeader.append(notificationsLink);
            if (profile) pageHeader.append(profile);
        } else if (page && (notificationsLink || profile)) {
            const accountBar = document.createElement("div");
            accountBar.className = "app-account-bar";
            if (notificationsLink) accountBar.append(notificationsLink);
            if (profile) accountBar.append(profile);
            page.prepend(accountBar);
        }

        if (notificationsLink) apiRequest("/api/v1/notifications")
            .then((data) => {
                const badge = notificationsLink.querySelector(".app-notification-badge");
                if (!badge) return;
                const unread = Number(data.unread_count) || 0;
                badge.textContent = unread > 99 ? "99+" : String(unread);
                badge.hidden = unread === 0;
                notificationsLink.setAttribute("aria-label", unread ? `${unread} unread notifications` : "Notifications");
            })
            .catch(() => {});
    }

    function createNavigationIcon(name) {
        const namespace = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(namespace, "svg");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("focusable", "false");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("fill", "none");
        svg.setAttribute("stroke", "currentColor");
        svg.setAttribute("stroke-width", "1.8");
        svg.setAttribute("stroke-linecap", "round");
        svg.setAttribute("stroke-linejoin", "round");

        const markup = {
            "layout-dashboard": '<rect x="3" y="3" width="7" height="9" rx="1"></rect><rect x="14" y="3" width="7" height="5" rx="1"></rect><rect x="14" y="12" width="7" height="9" rx="1"></rect><rect x="3" y="16" width="7" height="5" rx="1"></rect>',
            house: '<path d="m3 10 9-7 9 7"></path><path d="M5 9v12h14V9M9 21v-7h6v7"></path>',
            "user-round": '<circle cx="12" cy="8" r="4"></circle><path d="M5 21a7 7 0 0 1 14 0"></path>',
            users: '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="10" cy="7" r="4"></circle><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>',
            pill: '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path><path d="m8.5 8.5 7 7"></path>',
            boxes: '<path d="M2.97 12.92A2 2 0 0 0 2 14.63v3.24a2 2 0 0 0 .97 1.71l3 1.8a2 2 0 0 0 2.06 0L12 19v-5.5l-5-3-4.03 2.42Z"></path><path d="M12 13.5V19l3.97 2.38a2 2 0 0 0 2.06 0l3-1.8a2 2 0 0 0 .97-1.71v-3.24a2 2 0 0 0-.97-1.71L17 10.5l-5 3Z"></path><path d="M7.97 4.42A2 2 0 0 0 7 6.13v4.37l5 3 5-3V6.13a2 2 0 0 0-.97-1.71l-3-1.8a2 2 0 0 0-2.06 0l-3 1.8Z"></path>',
            grid: '<rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect>',
            factory: '<path d="M2 22V8l7 4V8l7 4V4h4v18Z"></path><path d="M6 22v-4h4v4M14 22v-4h4v4M18 8h3"></path>',
            ruler: '<path d="M21.3 8.7 15.3 2.7a1 1 0 0 0-1.4 0L2.7 13.9a1 1 0 0 0 0 1.4l6 6a1 1 0 0 0 1.4 0L21.3 10.1a1 1 0 0 0 0-1.4Z"></path><path d="m7.5 10.5 2 2m1-5 2 2m1-5 2 2m-7 10 2 2"></path>',
            truck: '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"></path><path d="M15 18H9M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"></path><circle cx="17" cy="18" r="2"></circle><circle cx="7" cy="18" r="2"></circle>',
            "shopping-cart": '<circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"></path>',
            receipt: '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"></path><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8M12 17.5v-11"></path>',
            bell: '<path d="M10.268 21a2 2 0 0 0 3.464 0"></path><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"></path>',
            "chart-column": '<path d="M3 3v16a2 2 0 0 0 2 2h16"></path><path d="M18 17V9M13 17V5M8 17v-3"></path>',
            settings: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2Z"></path><circle cx="12" cy="12" r="3"></circle>',
            history: '<path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"></path><path d="M3 3v5h5M12 7v5l3 2"></path>',
            audit: '<path d="M8 3h8l4 4v14H4V3h4Z"></path><path d="M8 11h8m-8 4h8m-8 4h5M16 3v5h5"></path>',
            "file-text": '<path d="M8 3h8l4 4v14H4V3h4Z"></path><path d="M8 11h8m-8 4h8m-8 4h5M16 3v5h5"></path>'
        };
        svg.innerHTML = markup[name] || "";
        return svg;
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
