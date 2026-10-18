(() => {
    const preferenceKey = "ms-contable-theme";
    const savedTheme = localStorage.getItem(preferenceKey);
    const theme = savedTheme === "light" ? "light" : "dark";

    document.documentElement.dataset.theme = theme;

    document.addEventListener("click", (event) => {
        const button = event.target instanceof Element && event.target.closest(".theme-toggle");
        if (!button) return;

        event.stopImmediatePropagation();
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = nextTheme;
        localStorage.setItem(preferenceKey, nextTheme);
    }, true);
})();
