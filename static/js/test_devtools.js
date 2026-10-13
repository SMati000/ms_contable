(() => {
    const root = document.getElementById("test-devtools");
    if (!root) return;

    const trigger = root.querySelector(".test-devtools-trigger");
    const panel = root.querySelector(".test-devtools-panel");
    const closeButton = root.querySelector(".test-devtools-close");
    const message = root.querySelector(".test-devtools-message");
    const counts = root.querySelector(".test-devtools-counts ul");
    const csrfToken = document.querySelector(
        '#test-devtools-csrf input[name="csrfmiddlewaretoken"]',
    )?.value;

    function setOpen(open) {
        panel.hidden = !open;
        trigger.setAttribute("aria-expanded", String(open));
        if (open) refreshCounts();
    }

    function renderCounts(items) {
        counts.replaceChildren();
        for (const item of items) {
            const name = document.createElement("li");
            const label = document.createElement("span");
            const total = document.createElement("span");
            label.textContent = item.nombre;
            total.textContent = Number(item.cantidad).toLocaleString("es-AR");
            name.append(label, total);
            if (item.sistema) {
                const system = document.createElement("span");
                system.className = "system-label";
                system.textContent = "Catálogo fijo";
                name.append(system, document.createElement("span"));
            }
            counts.append(name);
        }
    }

    async function send(url, method = "GET") {
        const options = {
            method,
            credentials: "same-origin",
            headers: { Accept: "application/json" },
        };
        if (method === "POST") {
            options.headers["X-CSRFToken"] = csrfToken || "";
        }
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "No se pudo completar la acción.");
        }
        return data;
    }

    async function refreshCounts() {
        message.textContent = "Actualizando cantidades…";
        try {
            const data = await send(root.dataset.statusUrl);
            renderCounts(data.counts);
            message.textContent = "Base de test lista para usar.";
        } catch {
            message.textContent = "No se pudieron consultar los datos de test.";
        }
    }

    async function runAction(button) {
        const action = button.dataset.action;
        if (action === "status") {
            await refreshCounts();
            return;
        }
        if ((action === "replace" || action === "clear") && !window.confirm(
            action === "clear"
                ? "Se borrarán empresas, empleados, conceptos, plantillas y liquidaciones de la base de test. ¿Continuar?"
                : "Se borrarán los datos de negocio actuales y se generará un conjunto nuevo. ¿Continuar?",
        )) return;

        const buttons = root.querySelectorAll(".test-devtools-actions button");
        buttons.forEach((item) => { item.disabled = true; });
        message.textContent = "Procesando…";
        try {
            const data = await send(button.dataset.url, "POST");
            renderCounts(data.counts);
            message.textContent = data.message;
        } catch {
            message.textContent = "No se pudo completar la acción. Revisá la conexión e intentá de nuevo.";
        } finally {
            buttons.forEach((item) => { item.disabled = false; });
        }
    }

    trigger.addEventListener("click", () => setOpen(panel.hidden));
    closeButton.addEventListener("click", () => setOpen(false));
    root.querySelector(".test-devtools-actions").addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        if (button) runAction(button);
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !panel.hidden) setOpen(false);
    });
})();
