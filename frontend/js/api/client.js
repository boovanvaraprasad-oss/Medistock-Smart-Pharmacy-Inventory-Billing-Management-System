const API_BASE_URL = "http://127.0.0.1:8000";
const CURRENT_USER_CACHE_KEY = "medistock_current_user";
let currentUserRequest = null;

function getDashboardForRole(role) {
    const roleDashboards = {
        pharmacist: "pharmacist_dashboard.html",
        inventory_executive: "inventory_dashboard.html",
        purchase_executive: "purchase_dashboard.html",
        store_manager: "store_manager_dashboard.html",
        compliance_officer: "compliance_dashboard.html"
    };

    return roleDashboards[role] || "dashboard.html";
}

function getCachedCurrentUser() {
    try {
        return JSON.parse(sessionStorage.getItem(CURRENT_USER_CACHE_KEY) || "null");
    } catch {
        sessionStorage.removeItem(CURRENT_USER_CACHE_KEY);
        return null;
    }
}

function cacheCurrentUser(user) {
    sessionStorage.setItem(CURRENT_USER_CACHE_KEY, JSON.stringify(user));
    window.dispatchEvent(new CustomEvent("medistock:current-user", { detail: user }));
}

function clearCachedCurrentUser() {
    sessionStorage.removeItem(CURRENT_USER_CACHE_KEY);
}

function getCurrentUser() {
    const cachedUser = getCachedCurrentUser();
    if (cachedUser) {
        if (!currentUserRequest) {
            requestCurrentUser().catch(() => {
                if (!localStorage.getItem("access_token")) {
                    clearCachedCurrentUser();
                    window.location.href = "/";
                }
            });
        }
        return Promise.resolve(cachedUser);
    }

    return requestCurrentUser();
}

function requestCurrentUser() {
    if (!currentUserRequest) {
        currentUserRequest = apiRequest("/api/v1/auth/me").finally(() => {
            currentUserRequest = null;
        });
    }
    return currentUserRequest;
}

async function readResponse(response) {
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}

async function loginUser(email, password) {
    const formData = new URLSearchParams();
    formData.set("username", email);
    formData.set("password", password);

    const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/token`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData.toString()
        }
    );

    return readResponse(response);
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
        throw new Error("No refresh token is available. Please log in again.");
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ refresh_token: refreshToken })
    });
    const data = await readResponse(response);

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data.access_token;
}

async function apiRequest(path, options = {}) {
    const sendRequest = (accessToken) => {
        const headers = new Headers(options.headers || {});
        headers.set("Authorization", `Bearer ${accessToken}`);

        return fetch(`${API_BASE_URL}${path}`, {
            ...options,
            headers
        });
    };

    let accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
        throw new Error("Please log in to continue.");
    }

    let response = await sendRequest(accessToken);
    if (response.status === 401) {
        try {
            accessToken = await refreshAccessToken();
        } catch (error) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            clearCachedCurrentUser();
            throw error;
        }

        response = await sendRequest(accessToken);
    }

    const data = await readResponse(response);
    if (path === "/api/v1/auth/me") {
        cacheCurrentUser(data);
    }
    return data;
}

async function logoutUser() {
    let accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");

    if (!accessToken || !refreshToken) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        clearCachedCurrentUser();
        return;
    }

    const sendLogout = (token) => fetch(
        `${API_BASE_URL}/api/v1/auth/logout`,
        {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        }
    );

    let response = await sendLogout(accessToken);
    if (response.status === 401) {
        try {
            accessToken = await refreshAccessToken();
        } catch (error) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            clearCachedCurrentUser();
            throw error;
        }

        response = await sendLogout(accessToken);
    }

    await readResponse(response);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    clearCachedCurrentUser();
}
