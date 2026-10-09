(function () {
    "use strict";

    const SELECTOR = 'select[id$="-concepto"]';

    function actualizarDetalles(select) {
        const detalle = select.closest(".inline-related");
        if (!detalle) return;

        const spanUnidad = detalle.querySelector(".unidad-display");
        const spanCategoria = detalle.querySelector(".categoria-display");
        const spanTipo = detalle.querySelector(".tipo-display");
        const spanGrupo = detalle.querySelector(".grupo-display");
        const spanIdentificador = detalle.querySelector(".inline_label");
        const fieldsetRegistro03 = detalle.querySelector(".registro03-fieldset");

        if (
            !spanUnidad ||
            !spanCategoria ||
            !spanTipo ||
            !spanGrupo ||
            !spanIdentificador ||
            !fieldsetRegistro03
        ) return;

        const conceptoId = select.value;

        if (!conceptoId) {
            spanTipo.textContent = "-";
            spanGrupo.textContent = "-";
            spanUnidad.textContent = "-";
            spanCategoria.textContent = "-";
            spanIdentificador.textContent = "";

            fieldsetRegistro03.style.display = "none";

            return;
        }

        const base = window.location.pathname.includes("/agregar/")
            ? "../concepto-detalles/"
            : "../../concepto-detalles/";

        fetch(base + conceptoId + "/", { credentials: "same-origin" })
            .then((r) => r.json())
            .then((data) => {
                spanUnidad.textContent = data.unidad || "no_encontrado";
                spanCategoria.textContent = data.categoria || "no_encontrado";
                spanTipo.textContent = data.tipo || "no_encontrado";
                spanGrupo.textContent = data.grupo || "-";

                spanIdentificador.textContent = data.identificador || "";

                fieldsetRegistro03.style.display = data.tiene_codigo_arca ? "" : "none";
            })
            .catch(() => {
                spanUnidad.textContent = "-";
                spanCategoria.textContent = "-";
                spanTipo.textContent = "-";
                spanGrupo.textContent = "-";
                spanIdentificador.textContent = "";

                fieldsetRegistro03.style.display = "none";
            });
    }

    function ajustarAlturaTextarea(textarea) {
        textarea.style.height = "auto";

        const maxHeight = parseFloat(
            getComputedStyle(textarea).maxHeight
        );

        textarea.style.height = `${Math.min(
            textarea.scrollHeight,
            maxHeight
        )}px`;
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.body.addEventListener("change", function (e) {
            if (e.target.matches(SELECTOR)) {
                actualizarDetalles(e.target);
            }
        });

        document
            .querySelectorAll(SELECTOR)
            .forEach(function (select) {
                actualizarDetalles(select);
            });

        document.body.addEventListener("input", function (e) {
            if (e.target.matches("#detalles-group .field-formula_base textarea")) {
                ajustarAlturaTextarea(e.target);
            }
        });

        document.querySelectorAll(
            "#detalles-group .field-formula_base textarea"
        ).forEach(ajustarAlturaTextarea);

    });
})();
