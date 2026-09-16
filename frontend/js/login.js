const loginForm = document.getElementById("loginForm");
const message = document.getElementById("message");

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const data = await loginUser(email, password);

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        message.textContent = "Login successful!";
    } catch (error) {
        message.textContent = error.message;
    }
});

const signupButton = document.getElementById("signupButton");

signupButton.addEventListener("click", () => {
    window.location.href = "signup.html";
});