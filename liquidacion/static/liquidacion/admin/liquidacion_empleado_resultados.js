(function () {
    "use strict";

    function actualizarResultados(resultados) {
        if (!resultados) return;

        Object.entries(resultados.totales || {}).forEach(([nombre, importe]) => {
            const campo = document.querySelector(
                `.liquidacion-wizard-totales .field-${nombre}_display .readonly`,
            );
            if (campo) campo.textContent = importe;
        });

        const detalles = resultados.detalles || {};
        document.querySelectorAll("#detalles-group .inline-related:not(.empty-form)")
            .forEach((fila) => {
                const concepto = fila.querySelector("select[id$='-concepto']")?.value;
                const importe = detalles[concepto];
                if (!importe) return;

                const base = fila.querySelector(".field-base_display .readonly");
                const valor = fila.querySelector(".field-importe_display .readonly");
                if (base) base.textContent = importe.base;
                if (valor) valor.textContent = importe.importe;
            });

        const bases = resultados.bases || {};
        document.querySelectorAll(
            "#resultados_bases_imponibles-group .inline-related:not(.empty-form), " +
            "#resultados_bases_imponibles-group tr.form-row:not(.empty-form)",
        ).forEach((fila) => {
            const id = fila.querySelector("input[name$='-id']")?.value;
            const importe = bases[id];
            if (importe === undefined) return;

            const campo = fila.querySelector("[name$='-importe']");
            const lectura = fila.querySelector(".field-importe_display .readonly");
            if (campo) campo.value = importe;
            if (lectura) lectura.textContent = importe;
        });
    }

    document.addEventListener("liquidacion:actualizar-resultados", (evento) => {
        actualizarResultados(evento.detail);
    });
})();
