document.addEventListener("DOMContentLoaded", function () {
    const empresaSelect = document.getElementById("id_empresa");

    if (empresaSelect) {
        const actualizarTooltipEmpresa = function () {
            const empresaSeleccionada = empresaSelect.selectedOptions[0];
            empresaSelect.title = empresaSeleccionada
                ? empresaSeleccionada.textContent.trim().replace(/\s+/g, " ")
                : "";
        };

        actualizarTooltipEmpresa();
        empresaSelect.addEventListener("change", actualizarTooltipEmpresa);
    }

    const button = document.getElementById("btn-generar-txt");

    if (!button) {
        return;
    }

    button.addEventListener("click", async function () {
        const response = await fetch(button.dataset.url, {
            method: "POST",
            headers: {
                "X-CSRFToken": button.dataset.csrfToken,
            },
        });

        if (!response.ok) {
            alert("Error al generar TXT!");
            return;
        }

        const blob = await response.blob();

        const disposition = response.headers.get("Content-Disposition");
        const match = disposition?.match(/filename="([^"]+)"/);
        const filename = match ? match[1] : "liquidacion.txt";

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");

        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();

        URL.revokeObjectURL(url);

        window.location.reload();
    });
});
