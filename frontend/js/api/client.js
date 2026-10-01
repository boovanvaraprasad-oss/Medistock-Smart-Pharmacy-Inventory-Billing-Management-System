const API_BASE_URL = "http://127.0.0.1:8000";

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
            throw error;
        }

        response = await sendRequest(accessToken);
    }

    return readResponse(response);
}

async function logoutUser() {
    let accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");

    if (!accessToken || !refreshToken) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
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
            throw error;
        }

        response = await sendLogout(accessToken);
    }

    await readResponse(response);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}
