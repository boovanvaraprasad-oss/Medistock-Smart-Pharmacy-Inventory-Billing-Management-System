const signupForm = document.getElementById("signupForm");
const backToLogin = document.getElementById("backToLogin");
const message = document.getElementById("message");

signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPassword").value;
    const confirmPassword =
        document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        message.textContent = "Passwords do not match.";
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
            message.textContent =
                data.detail || "Registration failed.";
            return;
        }

        message.textContent =
            "Account created successfully. Redirecting to login...";

        setTimeout(() => {
            window.location.href = "index.html";
        }, 1500);

    } catch (error) {
        console.error(error);
        message.textContent =
            "Unable to connect to the server.";
    }
});

backToLogin.addEventListener("click", () => {
    window.location.href = "index.html";
});