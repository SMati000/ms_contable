(function () {
    "use strict";

    const STEPS = [
        {
            title: "Empleado",
            description: "Revisá el empleado y la liquidación asociada.",
            selectors: [".liquidacion-wizard-empleado"],
        },
        {
            title: "Conceptos",
            description: "Aplicá una plantilla si corresponde y completá sus conceptos.",
            selectors: ["#liquidacion-plantilla", "#detalles-group"],
        },
        {
            title: "Datos complementarios",
            description: "Completá los datos adicionales, observaciones y tramos.",
            selectors: [
                ".liquidacion-wizard-complementarios",
                ".liquidacion-wizard-observaciones",
                "#situaciones_revista-group",
            ],
        },
        {
            title: "Resultados",
            description: "Revisá las bases imponibles y calculá los importes.",
            selectors: [
                "#resultados_bases_imponibles-group",
                ".liquidacion-wizard-totales",
            ],
        },
    ];

    let wizard = null;
    let guardando = false;

    function crearWizard(form, pasoInicial = 0) {
        const pasos = STEPS.map((configuracion) => ({
            ...configuracion,
            elementos: configuracion.selectors
                .map((selector) => form.querySelector(selector))
                .filter(Boolean),
        })).filter((paso) => paso.elementos.length);

        if (pasos.length < 2) {
            return null;
        }

        const primerElemento = pasos[0].elementos[0];
        const contenedor = document.createElement("section");
        contenedor.className = "liquidacion-wizard";
        contenedor.setAttribute("aria-label", "Pasos de la liquidación");

        const encabezado = document.createElement("div");
        encabezado.className = "liquidacion-wizard__header";

        const introduccion = document.createElement("div");
        introduccion.innerHTML =
            '<p class="liquidacion-wizard__eyebrow">Liquidación por empleado</p>' +
            '<p class="liquidacion-wizard__hint">Avanzá por los pasos para completar la liquidación.</p>' +
            '<p class="liquidacion-wizard__current" aria-live="polite"></p>';
        encabezado.append(introduccion);

        const ayuda = form.querySelector("[data-help-target='help-dialog']");
        if (ayuda) {
            encabezado.append(ayuda);
        }

        const navegacion = document.createElement("nav");
        navegacion.className = "liquidacion-wizard__navigation";
        navegacion.setAttribute("aria-label", "Pasos");

        const paneles = document.createElement("div");
        paneles.className = "liquidacion-wizard__panels";

        const botonesPaso = [];
        const panelesPaso = [];

        pasos.forEach((paso, indice) => {
            const botonPaso = document.createElement("button");
            botonPaso.type = "button";
            botonPaso.className = "liquidacion-wizard__step-link";
            botonPaso.dataset.step = String(indice);
            botonPaso.disabled = indice > pasoInicial;
            botonPaso.innerHTML =
                `<span class="liquidacion-wizard__step-number">${indice + 1}</span>` +
                `<span>${paso.title}</span>`;
            navegacion.append(botonPaso);
            botonesPaso.push(botonPaso);

            const panel = document.createElement("section");
            panel.className = "liquidacion-wizard__panel";
            panel.dataset.step = String(indice);
            panel.setAttribute("aria-labelledby", `liquidacion-wizard-title-${indice}`);

            const titulo = document.createElement("h2");
            titulo.className = "liquidacion-wizard__title";
            titulo.id = `liquidacion-wizard-title-${indice}`;
            titulo.textContent = paso.title;
            panel.append(titulo);

            const descripcion = document.createElement("p");
            descripcion.className = "liquidacion-wizard__description";
            descripcion.textContent = paso.description;
            panel.append(descripcion);

            const controles = document.createElement("div");
            controles.className = "liquidacion-wizard__controls";

            const anterior = document.createElement("button");
            anterior.type = "button";
            anterior.className = "button liquidacion-wizard__previous";
            anterior.textContent = "Anterior";
            anterior.dataset.stepAction = "previous";
            controles.append(anterior);

            const continuar = document.createElement("button");
            continuar.type = "button";
            continuar.className = "button default liquidacion-wizard__next";
            continuar.textContent = indice === pasos.length - 1
                ? "Volver a empleado"
                : "Continuar";
            continuar.dataset.stepAction = indice === pasos.length - 1
                ? "first"
                : "next";
            controles.append(continuar);
            panel.append(controles);

            paneles.append(panel);
            panelesPaso.push(panel);
        });

        contenedor.append(encabezado, navegacion, paneles);
        primerElemento.parentNode.insertBefore(contenedor, primerElemento);
        pasos.forEach((paso, indice) => {
            paso.elementos.forEach((elemento) => panelesPaso[indice].append(elemento));
        });

        const estado = {
            form,
            contenedor,
            botonesPaso,
            panelesPaso,
            titulos: pasos.map((paso) => paso.title),
            pasoActual: 0,
            visitados: new Set([0]),
        };

        form.noValidate = true;
        mostrarPaso(estado, Math.min(pasoInicial, panelesPaso.length - 1));
        return estado;
    }

    function mostrarPaso(estado, indice) {
        if (!estado || indice < 0 || indice >= estado.panelesPaso.length) {
            return;
        }

        estado.pasoActual = indice;
        estado.visitados.add(indice);

        estado.panelesPaso.forEach((panel, panelIndex) => {
            panel.hidden = panelIndex !== indice;
            const anterior = panel.querySelector(".liquidacion-wizard__previous");
            if (anterior) anterior.disabled = panelIndex === 0;
        });

        estado.botonesPaso.forEach((boton, botonIndex) => {
            boton.disabled = botonIndex > Math.max(...estado.visitados);
            if (botonIndex === indice) {
                boton.setAttribute("aria-current", "step");
            } else {
                boton.removeAttribute("aria-current");
            }
        });

        const indicador = estado.contenedor.querySelector(".liquidacion-wizard__current");
        if (indicador) {
            indicador.textContent = `Paso ${indice + 1} de ${estado.panelesPaso.length} · ${estado.titulos[indice]}`;
        }
    }

    function validarPaso(panel) {
        const controles = [...panel.querySelectorAll("input, select, textarea")];
        const invalido = controles.find((control) => (
            !control.disabled &&
            !control.closest(".empty-form") &&
            control.type !== "hidden" &&
            control.willValidate &&
            !control.validity.valid
        ));

        if (invalido) {
            invalido.reportValidity();
            invalido.focus();
            return false;
        }

        return true;
    }

    function mostrarEstado(mensaje, tipo = "success") {
        const estado = document.getElementById("liquidacion-form-status");
        if (!estado) return;

        estado.textContent = mensaje;
        estado.classList.toggle("is-error", tipo === "error");
        estado.classList.toggle("is-success", tipo === "success");
    }

    function limpiarErroresServidor(form) {
        form.querySelectorAll(".liquidacion-server-errors").forEach((lista) => lista.remove());
        form.querySelectorAll(".liquidacion-server-error").forEach((campo) => {
            campo.classList.remove("liquidacion-server-error", "errors");
        });
        form.querySelectorAll("[aria-invalid='true']").forEach((campo) => {
            campo.removeAttribute("aria-invalid");
        });
    }

    function mostrarErroresServidor(form, errores) {
        limpiarErroresServidor(form);
        let primerPanel = null;
        let primerControl = null;

        errores.forEach((error) => {
            const control = error.name && [...form.elements].find((elemento) => elemento.name === error.name);
            const grupo = error.group && document.getElementById(error.group);
            const destino = control
                ? control.closest("td") || control.closest(".form-row") || control.parentElement
                : grupo || wizard.contenedor;
            const lista = document.createElement("ul");
            lista.className = "errorlist liquidacion-server-errors";
            error.messages.forEach((mensaje) => {
                const item = document.createElement("li");
                item.textContent = mensaje;
                lista.append(item);
            });
            destino.append(lista);

            if (control) {
                control.setAttribute("aria-invalid", "true");
                destino.classList.add("liquidacion-server-error", "errors");
            }
            const panel = destino.closest(".liquidacion-wizard__panel");
            if (panel && (!primerPanel || panel.dataset.step < primerPanel.dataset.step)) {
                primerPanel = panel;
                primerControl = control;
            } else if (!primerPanel) {
                primerControl ||= control;
            }
        });

        if (primerPanel) {
            mostrarPaso(wizard, Number(primerPanel.dataset.step));
            primerControl?.focus();
            primerControl?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

    function ponerBotonesEnEspera(form, enEspera) {
        form.querySelectorAll(".submit-row input[type='submit']").forEach((boton) => {
            if (enEspera) {
                boton.dataset.originalValue = boton.value;
                boton.value = boton.name === "_calcular" ? "Calculando…" : "Guardando…";
                boton.disabled = true;
            } else {
                boton.value = boton.dataset.originalValue || boton.value;
                boton.disabled = false;
            }
        });
    }

    async function manejarEnvio(evento) {
        const form = evento.currentTarget;
        const submitter = evento.submitter || form.querySelector("input[name='_continue'], input[name='_calcular']");
        if (!submitter || !["_continue", "_calcular"].includes(submitter.name)) {
            return;
        }

        evento.preventDefault();
        if (guardando) return;

        const primerInvalido = wizard.panelesPaso
            .flatMap((panel, indice) => [...panel.querySelectorAll("input, select, textarea")]
                .map((control) => ({ control, indice })))
            .find(({ control }) => (
                !control.disabled &&
                !control.closest(".empty-form") &&
                control.type !== "hidden" &&
                control.willValidate &&
                !control.validity.valid
            ));

        if (primerInvalido) {
            mostrarPaso(wizard, primerInvalido.indice);
            primerInvalido.control.reportValidity();
            primerInvalido.control.focus();
            mostrarEstado("Revisá los campos obligatorios antes de guardar.", "error");
            return;
        }

        const datos = new FormData(form);
        datos.append(submitter.name, submitter.value);
        limpiarErroresServidor(form);
        guardando = true;
        ponerBotonesEnEspera(form, true);
        mostrarEstado(submitter.name === "_calcular" ? "Calculando la liquidación…" : "Guardando los cambios…");

        try {
            const response = await fetch(form.action || window.location.href, {
                method: "POST",
                body: datos,
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/html",
                },
            });

            const contentType = response.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const resultado = await response.json();
                if (resultado.ok) {
                    document.dispatchEvent(new CustomEvent(
                        "liquidacion:actualizar-resultados",
                        { detail: resultado.resultados },
                    ));
                    mostrarEstado(resultado.message);
                } else {
                    mostrarErroresServidor(form, resultado.errors || []);
                    mostrarEstado(resultado.message || "No se pudo completar la operación.", "error");
                }
            } else {
                mostrarEstado("No se pudo completar la operación. Volvé a intentarlo.", "error");
            }
        } catch (error) {
            mostrarEstado("No se pudo conectar con el servidor. Revisá la conexión e intentá de nuevo.", "error");
        } finally {
            guardando = false;
            const formularioActual = document.querySelector("#content-main form");
            if (formularioActual) ponerBotonesEnEspera(formularioActual, false);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        const form = document.querySelector("#content-main form");
        if (!form || !form.querySelector(".liquidacion-wizard-empleado")) return;

        wizard = crearWizard(form);
        form.addEventListener("submit", manejarEnvio);

        document.body.addEventListener("click", function (evento) {
            if (!(evento.target instanceof Element)) return;
            const botonPaso = evento.target.closest(".liquidacion-wizard__step-link");
            if (botonPaso && wizard) {
                const indice = Number(botonPaso.dataset.step);
                if (indice > wizard.pasoActual && !validarPaso(wizard.panelesPaso[wizard.pasoActual])) {
                    return;
                }
                mostrarPaso(wizard, indice);
                return;
            }

            const accionPaso = evento.target.closest("[data-step-action]");
            if (!accionPaso || !wizard) return;

            const accion = accionPaso.dataset.stepAction;
            if (accion === "previous") {
                mostrarPaso(wizard, wizard.pasoActual - 1);
            } else if (accion === "first") {
                mostrarPaso(wizard, 0);
            } else if (validarPaso(wizard.panelesPaso[wizard.pasoActual])) {
                mostrarPaso(wizard, wizard.pasoActual + 1);
            }
        });
    });
})();
