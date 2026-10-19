(() => {
    const sidebar = document.getElementById("nav-sidebar");
    if (!sidebar) return;
    const toggle = document.getElementById("toggle-nav-sidebar");

    const chrome = [
        document.getElementById("header"),
        document.querySelector(".breadcrumbs"),
    ].filter(Boolean);
    let positionFrame = 0;

    function positionSidebar() {
        positionFrame = 0;

        const viewport = window.visualViewport;
        const viewportTop = viewport?.offsetTop ?? 0;
        const viewportHeight = viewport?.height ?? window.innerHeight;
        const viewportBottom = viewportTop + viewportHeight;
        let contentTop = viewportTop;

        chrome.forEach((element) => {
            const rect = element.getBoundingClientRect();
            if (rect.top <= contentTop && rect.bottom > contentTop) {
                contentTop = Math.min(rect.bottom, viewportBottom);
            }
        });

        const availableHeight = Math.max(1, viewportBottom - contentTop);
        const maxHeight = Math.min(
            Math.max(1, viewportHeight - 116),
            Math.max(1, availableHeight - 16)
        );

        sidebar.style.top = `${contentTop + availableHeight / 2}px`;
        sidebar.style.height = `${maxHeight}px`;
        sidebar.style.maxHeight = `${maxHeight}px`;

        if (toggle) {
            const sidebarRect = sidebar.getBoundingClientRect();
            toggle.style.top = `${sidebarRect.top}px`;
            toggle.style.height = `${sidebarRect.height}px`;
        }
    }

    function schedulePosition() {
        if (positionFrame) return;
        positionFrame = requestAnimationFrame(positionSidebar);
    }

    const chromeResizeObserver = typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(schedulePosition);
    chrome.forEach((element) => chromeResizeObserver?.observe(element));
    chromeResizeObserver?.observe(sidebar);

    window.addEventListener("resize", schedulePosition, { passive: true });
    window.addEventListener("scroll", schedulePosition, { capture: true, passive: true });
    document.addEventListener("scroll", schedulePosition, { capture: true, passive: true });
    window.visualViewport?.addEventListener("resize", schedulePosition, { passive: true });
    window.visualViewport?.addEventListener("scroll", schedulePosition, { passive: true });
    schedulePosition();
})();
