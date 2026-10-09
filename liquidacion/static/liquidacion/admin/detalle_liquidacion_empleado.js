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

    async function aplicarPlantilla(plantillaId, urlTemplate) {
        if (!plantillaId) {
            return;
        }

        const url = urlTemplate.replace(
            "/0/",
            `/${plantillaId}/`,
        );

        const response = await fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
        });

        if (!response.ok) {
            throw new Error(
                "No se pudieron obtener los detalles de la plantilla."
            );
        }

        const data = await response.json();

        const managementForm = document.querySelector(
            'input[name="detalles-TOTAL_FORMS"]',
        );

        if (!managementForm) {
            throw new Error(
                "No se encontró el management form del formset."
            );
        }

        const prefix = managementForm.name.replace(
            "-TOTAL_FORMS",
            "",
        );

        const emptyForm = document.querySelector(
            `#${prefix}-empty`,
        );

        if (!emptyForm) {
            throw new Error(
                "No se encontró el formulario vacío del formset."
            );
        }

        for (const detalle of data.detalles) {
            const formIndex = Number(managementForm.value);

            const row = emptyForm.cloneNode(true);

            row.removeAttribute("id");
            row.classList.remove("empty-form");
            row.classList.add("form-row");

            row.innerHTML = row.innerHTML.replaceAll(
                "__prefix__",
                formIndex,
            );

            emptyForm.parentNode.insertBefore(
                row,
                emptyForm,
            );

            const concepto = row.querySelector(
                `[name="${prefix}-${formIndex}-concepto"]`,
            );

            const unidades = row.querySelector(
                `[name="${prefix}-${formIndex}-unidades"]`,
            );

            const formulaBase = row.querySelector(
                `[name="${prefix}-${formIndex}-formula_base"]`,
            );

            const cantidad = row.querySelector(
                `[name="${prefix}-${formIndex}-cantidad"]`,
            );

            const unidadesLsd = row.querySelector(
                `[name="${prefix}-${formIndex}-unidades_lsd"]`,
            );

            const debitoCredito = row.querySelector(
                `[name="${prefix}-${formIndex}-debito_credito"]`,
            );

            const periodoAjusteRetroactivo = row.querySelector(
                `[name="${prefix}-${formIndex}-periodo_ajuste_retroactivo"]`,
            );

            if (concepto) {
                concepto.value = detalle.concepto;

                // Esto reutiliza la lógica existente que obtiene
                // y muestra la unidad.
                concepto.dispatchEvent(
                    new Event("change", {
                        bubbles: true,
                    }),
                );
            }

            if (unidades) {
                unidades.value = detalle.unidades;
            }

            if (formulaBase) {
                formulaBase.value = detalle.formula_base;
                ajustarAlturaTextarea(formulaBase);
            }

            if (cantidad) {
                cantidad.value = detalle.cantidad;
            }

            if (unidadesLsd) {
                unidadesLsd.value = detalle.unidades_lsd;
            }

            if (debitoCredito) {
                debitoCredito.value = detalle.debito_credito;
            }

            if (periodoAjusteRetroactivo) {
                periodoAjusteRetroactivo.value =
                    detalle.periodo_ajuste_retroactivo ?? "";
            }

            managementForm.value = formIndex + 1;
        }
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

            // Datos adicionales
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

            // Observaciones
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

        // Permite que otros scripts reaccionen al cambio.
        field.dispatchEvent(
            new Event("change", {
                bubbles: true,
            }),
        );
    }

    document.addEventListener("DOMContentLoaded", function () {
        // Delegación de eventos: funciona con filas agregadas dinámicamente
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

        const aplicarPlantillaButton =
            document.getElementById("aplicar-plantilla");

        if (aplicarPlantillaButton) {
            aplicarPlantillaButton.addEventListener(
                "click",
                async function () {
                    const plantillaId =
                        document.getElementById(
                            "plantilla-select",
                        ).value;

                    try {
                        await aplicarPlantilla(
                            plantillaId,
                            aplicarPlantillaButton.dataset.urlTemplate,
                        );
                    } catch (error) {
                        console.error(
                            "Error al aplicar la plantilla:",
                            error,
                        );
                    }
                },
            );
        }

        const boton = document.querySelector("#btn-liq-previa");
        if (boton) {
            boton.addEventListener(
                "click",
                async () => {
                    const url = boton.dataset.url;

                    if (!url) {
                        return;
                    }

                    boton.disabled = true;

                    await completarConLiqPrevia(boton, url);
                }
            )
        }

    });
})();
