(() => {
    const applySavedTheme = () => {
        document.documentElement.dataset.theme = localStorage.getItem("medistock_theme") === "dark" ? "dark" : "light";
    };
    applySavedTheme();
    window.addEventListener("storage", (event) => {
        if (event.key === "medistock_theme") applySavedTheme();
    });
})();
