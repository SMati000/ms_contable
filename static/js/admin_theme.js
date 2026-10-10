(() => {
    const savedTheme = localStorage.getItem("theme");
    const systemTheme = window.matchMedia?.("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    const theme = savedTheme === "light" || savedTheme === "dark" ? savedTheme : systemTheme;

    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);

    document.addEventListener("click", (event) => {
        const button = event.target instanceof Element && event.target.closest(".theme-toggle");
        if (!button) return;

        event.stopImmediatePropagation();
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = nextTheme;
        localStorage.setItem("theme", nextTheme);
    }, true);
})();
