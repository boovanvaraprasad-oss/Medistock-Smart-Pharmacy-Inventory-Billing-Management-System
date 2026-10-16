const loginForm = document.getElementById("loginForm");
const message = document.getElementById("message");
const checkSessionButton = document.getElementById("checkSessionButton");
const logoutButton = document.getElementById("logoutButton");
const signupButton = document.getElementById("signupButton");

async function checkSession() {
    try {
        await apiRequest("/api/v1/auth/me");
        message.textContent = "Your protected session is active.";
    } catch (error) {
        message.textContent = error.message;
    }
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const data = await loginUser(email, password);

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        window.location.href = "dashboard.html";
    } catch (error) {
        message.textContent = error.message;
    }
});

checkSessionButton.addEventListener("click", checkSession);

logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;

    try {
        await logoutUser();
        checkSessionButton.hidden = true;
        logoutButton.hidden = true;
        message.textContent = "Logged out successfully.";
    } catch (error) {
        message.textContent = error.message;
    } finally {
        logoutButton.disabled = false;
    }
});

signupButton.addEventListener("click", () => {
    window.location.href = "signup.html";
});