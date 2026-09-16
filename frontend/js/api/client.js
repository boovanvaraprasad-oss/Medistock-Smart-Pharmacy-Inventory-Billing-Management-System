const API_BASE_URL = "http://127.0.0.1:8000";

async function loginUser(email, password) {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/login`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Login failed");
    }

    return data;
}