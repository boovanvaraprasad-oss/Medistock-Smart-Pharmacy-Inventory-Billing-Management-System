const signupForm = document.getElementById("signupForm");
const backToLogin = document.getElementById("backToLogin");
const message = document.getElementById("message");

function showErrorMessage(text) {
    message.className = "message message-error";
    message.textContent = text;
}

function showSuccessMessage(text) {
    message.className = "message message-success";
    message.textContent = text;
}

signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPassword").value;
    const confirmPassword =
        document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        showErrorMessage("Passwords do not match.");
        return;
    }

    try {
        const response = await fetch("/api/v1/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showErrorMessage(data.detail || "Registration failed.");
            return;
        }

        showSuccessMessage(
            "Account created successfully. Opening your MediStock workspace…"
        );

        try {
            const tokens = await loginUser(email, password);
            sessionStorage.removeItem("medistock_current_user");
            localStorage.setItem("access_token", tokens.access_token);
            localStorage.setItem("refresh_token", tokens.refresh_token);
            await getCurrentUser();
            window.location.replace("/home.html");
        } catch {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            sessionStorage.removeItem("medistock_current_user");
            showSuccessMessage(
                "Your account was created. Please sign in to continue."
            );
            window.setTimeout(() => {
                window.location.href = "/login.html";
            }, 1800);
        }

    } catch (error) {
        console.error(error);
        showErrorMessage("Unable to connect to the server.");
    }
});

backToLogin.addEventListener("click", () => {
    window.location.href = "/login.html";
});
