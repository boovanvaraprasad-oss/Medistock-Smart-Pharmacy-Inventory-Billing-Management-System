const form = document.getElementById("profileForm");
const message = document.getElementById("profileMessage");
const saveButton = document.getElementById("saveProfile");

function roleLabel(role) {
    return (role || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function initializeProfile() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/";
        return;
    }
    try {
        const user = await getCurrentUser();
        document.getElementById("fullName").value = user.full_name || "";
        document.getElementById("email").value = user.email || "";
        document.getElementById("phone").value = user.phone || "";
        document.getElementById("role").value = roleLabel(user.role);
    } catch (error) {
        message.textContent = error.message || "Could not load your profile.";
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    saveButton.disabled = true;
    message.textContent = "Saving profile…";
    try {
        const savedProfile = await apiRequest("/api/v1/auth/me/profile", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                full_name: document.getElementById("fullName").value.trim(),
                phone: document.getElementById("phone").value.trim()
            })
        });
        message.textContent = "Profile saved. The owner can now see these details in Staff & Users.";
        const cachedUser = JSON.parse(sessionStorage.getItem("medistock_current_user") || "null");
        if (cachedUser) {
            sessionStorage.setItem("medistock_current_user", JSON.stringify({ ...cachedUser, ...savedProfile }));
        }
    } catch (error) {
        message.textContent = error.message || "Could not save your profile.";
    } finally {
        saveButton.disabled = false;
    }
});

initializeProfile();
