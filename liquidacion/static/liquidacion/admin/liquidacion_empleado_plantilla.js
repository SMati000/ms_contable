(function () {
    "use strict";

    async function aplicarPlantilla(boton) {
        const selector = document.getElementById("plantilla-select");
        const feedback = document.getElementById("plantilla-feedback");
        const plantillaId = selector?.value;

        if (!plantillaId) {
            feedback.textContent = "Seleccioná una plantilla para continuar.";
            feedback.hidden = false;
            feedback.classList.add("is-error");
            selector?.focus();
            return;
        }

        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.textContent = "Aplicando…";
        feedback.hidden = true;

        try {
            const url = boton.dataset.urlTemplate.replace("/0/", `/${plantillaId}/`);
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) {
                throw new Error("No se pudieron obtener los detalles de la plantilla.");
            }

            const data = await response.json();
            if (!data.detalles.length) {
                feedback.textContent = "La plantilla no contiene conceptos para aplicar.";
                feedback.classList.remove("is-error");
                feedback.hidden = false;
                return;
            }

            const totalForms = document.querySelector('input[name="detalles-TOTAL_FORMS"]');
            const emptyForm = document.getElementById("detalles-empty");
            if (!totalForms || !emptyForm) {
                throw new Error("No se encontró el formulario para agregar conceptos.");
            }

            const prefix = totalForms.name.replace("-TOTAL_FORMS", "");
            const existentes = new Set();
            document.querySelectorAll("#detalles-group .inline-related:not(.empty-form)")
                .forEach((fila) => {
                    if (fila.querySelector("input[name$='-DELETE']")?.checked) return;
                    const concepto = fila.querySelector("select[id$='-concepto']")?.value;
                    if (concepto) existentes.add(concepto);
                });

            let agregados = 0;
            let omitidos = 0;
            let primeraFila = null;

            for (const detalle of data.detalles) {
                const conceptoId = String(detalle.concepto);
                if (existentes.has(conceptoId)) {
                    omitidos += 1;
                    continue;
                }

                const indice = Number(totalForms.value);
                const fila = emptyForm.cloneNode(true);
                fila.removeAttribute("id");
                fila.classList.remove("empty-form");
                fila.classList.add("form-row");
                fila.innerHTML = fila.innerHTML.replaceAll("__prefix__", indice);
                emptyForm.parentNode.insertBefore(fila, emptyForm);

                const campo = (nombre) => fila.querySelector(
                    `[name="${prefix}-${indice}-${nombre}"]`,
                );
                const concepto = campo("concepto");
                if (concepto) {
                    concepto.value = conceptoId;
                    concepto.dispatchEvent(new Event("change", { bubbles: true }));
                }

                const valores = {
                    unidades: detalle.unidades,
                    formula_base: detalle.formula_base,
                    cantidad: detalle.cantidad ?? "",
                    unidades_lsd: detalle.unidades_lsd ?? "",
                    debito_credito: detalle.debito_credito ?? "",
                    periodo_ajuste_retroactivo: detalle.periodo_ajuste_retroactivo ?? "",
                };
                Object.entries(valores).forEach(([nombre, valor]) => {
                    const input = campo(nombre);
                    if (input) input.value = valor;
                });
                campo("formula_base")?.dispatchEvent(new Event("input", { bubbles: true }));

                totalForms.value = String(indice + 1);
                existentes.add(conceptoId);
                agregados += 1;
                primeraFila ||= fila;
            }

            feedback.textContent = omitidos
                ? `Se agregaron ${agregados} conceptos. Se omitieron ${omitidos} repetidos.`
                : agregados
                    ? `Se agregaron ${agregados} conceptos de la plantilla.`
                    : "La plantilla ya estaba aplicada; no se agregaron conceptos repetidos.";
            feedback.classList.remove("is-error");
            feedback.hidden = false;

            if (primeraFila) {
                primeraFila.scrollIntoView({ behavior: "smooth", block: "start" });
                primeraFila.querySelector("select[id$='-concepto']")?.focus({ preventScroll: true });
            }
        } catch (error) {
            feedback.textContent = error.message || "No se pudo aplicar la plantilla.";
            feedback.classList.add("is-error");
            feedback.hidden = false;
        } finally {
            boton.disabled = false;
            boton.textContent = textoOriginal;
        }
    }

    document.addEventListener("click", function (evento) {
        if (!(evento.target instanceof Element)) return;
        const boton = evento.target.closest("#aplicar-plantilla");
        if (boton) aplicarPlantilla(boton);
    });
})();
