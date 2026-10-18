(function () {
    "use strict";

    function completarTramosSituacionRevista(tramos) {
        const totalForms = document.querySelector(
            'input[name="situaciones_revista-TOTAL_FORMS"]',
        );

        if (!totalForms) {
            throw new Error(
                "No se encontró el formset de tramos de situación de revista.",
            );
        }

        const prefix = totalForms.name.replace("-TOTAL_FORMS", "");
        const emptyForm = document.querySelector(`#${prefix}-empty`);

        function obtenerFila(index) {
            const field = document.querySelector(
                `[name="${prefix}-${index}-codigo_situacion"]`,
            );

            return field?.closest(".inline-related, .form-row") ?? null;
        }

        for (let index = 0; index < tramos.length; index += 1) {
            let row = obtenerFila(index);

            if (!row) {
                if (!emptyForm) {
                    throw new Error(
                        "No se encontró el formulario vacío de tramos de situación de revista.",
                    );
                }

                row = emptyForm.cloneNode(true);
                row.removeAttribute("id");
                row.classList.remove("empty-form");
                row.classList.add("form-row");
                row.innerHTML = row.innerHTML.replaceAll(
                    "__prefix__",
                    index,
                );
                emptyForm.parentNode.insertBefore(row, emptyForm);
                totalForms.value = String(index + 1);
            }

            const codigoSituacion = row.querySelector(
                `[name="${prefix}-${index}-codigo_situacion"]`,
            );
            const diaInicio = row.querySelector(
                `[name="${prefix}-${index}-dia_inicio"]`,
            );
            const eliminar = row.querySelector(
                `[name="${prefix}-${index}-DELETE"]`,
            );

            if (!codigoSituacion || !diaInicio) {
                throw new Error(
                    "No se encontraron los campos de un tramo de situación de revista.",
                );
            }

            if (eliminar) {
                eliminar.checked = false;
                row.style.display = "";
            }

            codigoSituacion.value = tramos[index].codigo_situacion ?? "";
            diaInicio.value = tramos[index].dia_inicio ?? "";
        }

        const cantidadForms = Number(totalForms.value);

        for (let index = tramos.length; index < cantidadForms; index += 1) {
            const row = obtenerFila(index);
            const eliminar = row?.querySelector(
                `[name="${prefix}-${index}-DELETE"]`,
            );

            if (eliminar) {
                eliminar.checked = true;
                row.style.display = "none";
            }
        }
    }

    function completarDetracciones(importeDetracciones) {
        if (importeDetracciones === null || importeDetracciones === undefined) {
            return;
        }

        const filaDetracciones = Array.from(
            document.querySelectorAll(".field-base_imponible_display"),
        ).find(
            (field) => field.textContent.trim() === "Detracciones",
        )?.closest(".inline-related, .form-row");

        const importe = filaDetracciones?.querySelector(
            'input[name$="-importe"]',
        );

        if (!importe) {
            console.warn(
                "No se encontró el resultado de la base imponible de detracciones.",
            );
            return;
        }

        setField(importe.name, importeDetracciones);
    }

    async function completarConLiqPrevia(boton, url) {
        try {
            const response = await fetch(url, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
            });

            if (!response.ok) {
                throw new Error(
                    "No se pudo obtener la liquidación previa."
                );
            }

            const data = await response.json();

            if (!data.liq_previa) {
                alert(
                    "No existe una liquidación previa para este empleado."
                );
                return;
            }

            const campos = data.liq_previa;

            setField(
                "cantidad_dias_proporcionar_tope",
                campos.cantidad_dias_proporcionar_tope,
            );
            setField(
                "unidad_tiempo_trabajado",
                campos.unidad_tiempo_trabajado,
            );
            setField(
                "tiempo_trabajado",
                campos.tiempo_trabajado,
            );

            completarTramosSituacionRevista(
                campos.tramos_situacion_revista ?? [],
            );
            completarDetracciones(campos.detracciones);

            setField(
                "codigo_situacion",
                campos.codigo_situacion,
            );
            setField(
                "codigo_condicion",
                campos.codigo_condicion,
            );
            setField(
                "codigo_actividad",
                campos.codigo_actividad,
            );
            setField(
                "codigo_modalidad_contratacion",
                campos.codigo_modalidad_contratacion,
            );
            setField(
                "codigo_siniestrado",
                campos.codigo_siniestrado,
            );
            setField(
                "codigo_localidad",
                campos.codigo_localidad,
            );

            setField(
                "porcentaje_aporte_adicional_ss",
                campos.porcentaje_aporte_adicional_ss,
            );
            setField(
                "porcentaje_contrib_tarea_diferencial",
                campos.porcentaje_contrib_tarea_diferencial,
            );
            setField(
                "remuneracion_maternidad_anses",
                campos.remuneracion_maternidad_anses,
            );

            setField(
                "cantidad_adherentes_obra_social",
                campos.cantidad_adherentes_obra_social,
            );
            setField(
                "aporte_adicional_obra_social",
                campos.aporte_adicional_obra_social,
            );
            setField(
                "contrib_adicional_obra_social",
                campos.contrib_adicional_obra_social,
            );

            setField(
                "base_calc_diferencial_aportes_obra_social_fsr",
                campos.base_calc_diferencial_aportes_obra_social_fsr,
            );
            setField(
                "base_calc_diferencial_contrib_obra_social_fsr",
                campos.base_calc_diferencial_contrib_obra_social_fsr,
            );
            setField(
                "base_calc_diferencial_ley_riesgos_trabajo",
                campos.base_calc_diferencial_ley_riesgos_trabajo,
            );
            setField(
                "base_calc_diferencial_aportes_seg_social",
                campos.base_calc_diferencial_aportes_seg_social,
            );
            setField(
                "base_calc_diferencial_contrib_seg_social",
                campos.base_calc_diferencial_contrib_seg_social,
            );

            setField(
                "observaciones_recibo",
                campos.observaciones_recibo,
            );
            setField(
                "observaciones_lsd",
                campos.observaciones_lsd,
            );
        } catch (error) {
            console.error(error);
            alert(
                "Ocurrió un error al obtener la liquidación previa."
            );
        } finally {
            boton.disabled = false;
        }
    }

    function setField(name, value) {
        const field = document.querySelector(
            `[name="${name}"]`,
        );

        if (!field) {
            console.warn(
                `No se encontró el campo "${name}".`,
            );
            return;
        }

        field.value = value ?? "";
        field.dispatchEvent(
            new Event("change", {
                bubbles: true,
            }),
        );
    }

    document.addEventListener("click", async function (evento) {
        if (!(evento.target instanceof Element)) return;
        const boton = evento.target.closest("#btn-liq-previa");
        if (!boton) return;

        const url = boton.dataset.url;
        if (!url) return;

        boton.disabled = true;
        await completarConLiqPrevia(boton, url);
    });
})();
