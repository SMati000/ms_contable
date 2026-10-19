(() => {
    const sidebar = document.getElementById("nav-sidebar");
    const filter = document.getElementById("nav-filter");
    const content = document.getElementById("nav-sidebar-content");
    if (!sidebar || !filter || !content) return;

    const categories = [...content.querySelectorAll(":scope > .module")];
    const emptyState = document.createElement("div");
    emptyState.className = "nav-filter-empty";
    emptyState.setAttribute("role", "status");
    emptyState.textContent = "No hay resultados";
    emptyState.hidden = true;
    filter.insertAdjacentElement("afterend", emptyState);

    function updateCategoryVisibility() {
        const hasFilter = Boolean(filter.value);
        let hasVisibleCategories = false;

        categories.forEach((category) => {
            const hasVisibleModels = [...category.querySelectorAll('th[scope="row"]')]
                .some((heading) => heading.closest("tr").style.display !== "none");
            category.hidden = hasFilter && !hasVisibleModels;
            hasVisibleCategories ||= !category.hidden;
        });

        emptyState.hidden = !hasFilter || hasVisibleCategories;
    }

    ["input", "change", "keyup"].forEach((eventName) => {
        filter.addEventListener(eventName, updateCategoryVisibility);
    });

    updateCategoryVisibility();
})();
