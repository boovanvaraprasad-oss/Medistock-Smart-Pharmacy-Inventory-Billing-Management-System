const themeToggle = document.getElementById("themeToggle");
const settingsStatus = document.getElementById("settingsStatus");

themeToggle.checked = localStorage.getItem("medistock_theme") === "dark";

themeToggle.addEventListener("change", () => {
    const theme = themeToggle.checked ? "dark" : "light";
    localStorage.setItem("medistock_theme", theme);
    document.documentElement.dataset.theme = theme;
    settingsStatus.textContent = `${theme === "dark" ? "Dark" : "Light"} theme applied.`;
});
