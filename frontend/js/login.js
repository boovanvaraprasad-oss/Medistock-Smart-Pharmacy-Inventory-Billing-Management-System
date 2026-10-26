const loginForm = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const forgotPasswordLink = document.getElementById("forgotPasswordLink");
const loginButton = document.getElementById("loginButton");
const message = document.getElementById("message");

function showMessage(text) {
    message.textContent = text;
    message.hidden = !text;
}

forgotPasswordLink.addEventListener("click", (event) => {
    event.preventDefault();
    showMessage("Password reset is not available yet. Please contact your MediStock owner.");
});

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("");

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    loginButton.disabled = true;
    loginButton.textContent = "Signing in…";
    let tokensWereSaved = false;

    try {
        const data = await loginUser(email, password);

        sessionStorage.removeItem("medistock_current_user");
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        tokensWereSaved = true;

        const currentUser = await getCurrentUser();
        const destination = getDashboardForRole(currentUser.role);
        window.location.href = destination;
    } catch (error) {
        if (tokensWereSaved) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            sessionStorage.removeItem("medistock_current_user");
        }
        showMessage(error.message || "Unable to sign in. Check your details and try again.");
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }
});
