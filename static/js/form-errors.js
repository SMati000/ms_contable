(() => {
    let resizeHandler = null;

    function initializeFormErrors() {
        document.querySelectorAll(".error-summary-popup").forEach((popup) => popup.remove());
        document.querySelectorAll(".error-summary-placeholder").forEach((placeholder) => placeholder.remove());
        document.body.classList.remove("error-summary-active");
        if (resizeHandler) {
            window.removeEventListener("resize", resizeHandler);
            resizeHandler = null;
        }

        const allErrorLists = Array.from(document.querySelectorAll("form ul.errorlist"));
        const loginForm = document.querySelector("#login-form");
        const form = allErrorLists[0]?.closest("form") || loginForm;
        const errorLists = form ? Array.from(form.querySelectorAll("ul.errorlist")) : [];
        const summaryNote = form?.querySelector(".errornote")
            || document.querySelector(".errornote");

        if (document.body.classList.contains("login")) {
            summaryNote?.setAttribute("role", "alert");
            return;
        }

        if (!form || (!errorLists.length && !summaryNote)) {
            return;
        }

        const placeholder = summaryNote || document.createElement("div");
        const breadcrumbs = document.querySelector(".breadcrumbs");
        const formErrors = [];
        let tooltipIndex = 0;

        placeholder.classList.add("error-summary-placeholder");
        placeholder.setAttribute("aria-hidden", "true");

        if (breadcrumbs) {
            breadcrumbs.after(placeholder);
        } else {
            const heading = form.closest("#content")?.querySelector("h1");
            (heading || form).before(placeholder);
        }

        function getFieldLabel(errorList) {
            if (errorList.classList.contains("nonfield")) {
                return null;
            }

            let container = errorList.parentElement;
            while (container && container !== form) {
                const labels = container.querySelectorAll("label[for]");
                if (labels.length === 1) {
                    return labels[0];
                }
                if (labels.length > 1) {
                    return null;
                }
                container = container.parentElement;
            }

            return null;
        }

        function createTooltip(messages, options = {}) {
            const wrapper = document.createElement("span");
            wrapper.className = `error-tooltip ${options.className || ""}`.trim();

            const button = document.createElement("button");
            button.type = "button";
            button.className = "error-tooltip__trigger";
            const icon = document.createElement("span");
            icon.className = "error-tooltip__icon";
            icon.textContent = "!";
            button.append(icon);
            button.setAttribute("aria-label", options.label);
            button.setAttribute("aria-expanded", "false");

            const content = document.createElement("div");
            content.className = "error-tooltip__content";
            content.id = options.id || `form-error-tooltip-${tooltipIndex++}`;
            content.setAttribute("role", "tooltip");
            button.setAttribute("aria-describedby", content.id);

            const heading = document.createElement("strong");
            heading.textContent = options.heading;

            const details = document.createElement("ul");
            messages.forEach((message) => {
                const item = document.createElement("li");
                item.textContent = message;
                details.append(item);
            });

            content.append(heading, details);
            wrapper.append(button, content);

            const syncExpanded = () => {
                const isVisible = wrapper.matches(":hover, :focus-within")
                    || wrapper.classList.contains("is-open");
                button.setAttribute("aria-expanded", String(isVisible));
            };
            const updatePlacement = () => {
                content.classList.toggle(
                    "error-tooltip__content--right",
                    button.getBoundingClientRect().left > window.innerWidth / 2,
                );
            };

            wrapper.addEventListener("mouseenter", () => {
                updatePlacement();
                syncExpanded();
            });
            wrapper.addEventListener("mouseleave", syncExpanded);
            wrapper.addEventListener("focusin", () => {
                updatePlacement();
                syncExpanded();
            });
            wrapper.addEventListener("focusout", syncExpanded);
            button.addEventListener("click", () => {
                wrapper.classList.toggle("is-open");
                syncExpanded();
            });
            wrapper.addEventListener("keydown", (event) => {
                if (event.key === "Escape") {
                    wrapper.classList.remove("is-open");
                    button.blur();
                    syncExpanded();
                }
            });

            return wrapper;
        }

        errorLists.forEach((errorList) => {
            const messages = Array.from(errorList.children)
                .filter((item) => item.matches("li"))
                .map((item) => item.textContent.trim())
                .filter(Boolean);

            const label = getFieldLabel(errorList);
            const labelText = label?.textContent.trim().replace(/:\s*$/, "");

            messages.forEach((message) => {
                formErrors.push(labelText ? `${labelText}: ${message}` : message);
            });

            if (messages.length && label) {
                const fieldTooltip = createTooltip(messages, {
                    className: "error-tooltip--field",
                    heading: labelText,
                    id: errorList.id,
                    label: `Ver error${messages.length === 1 ? "" : "es"} de ${labelText}`,
                });
                label.before(fieldTooltip);
            }

            errorList.remove();
        });

        const loginFailure = form.id === "login-form" && !errorLists.length && summaryNote;
        if (loginFailure) {
            formErrors.push(summaryNote.textContent.trim());
        }

        const uniqueErrors = Array.from(new Set(formErrors));
        if (!uniqueErrors.length) {
            placeholder.remove();
            return;
        }

        const summaryText = (loginFailure
            ? "No se pudo iniciar sesión:"
            : errorLists.length
                ? "Completá o corregí los datos indicados:"
                : summaryNote?.textContent || "Revisá los datos indicados:")
            .trim()
            .replace(/[\s.!?;:]+$/u, ":");
        const summary = document.createElement("div");
        summary.className = "error-summary-popup";
        summary.setAttribute("role", "alert");
        summary.setAttribute("aria-live", "assertive");
        summary.setAttribute("aria-atomic", "true");

        const message = document.createElement("span");
        message.className = "error-summary-popup__message";
        message.textContent = summaryText;

        const allErrorsTooltip = createTooltip(uniqueErrors, {
            className: "error-tooltip--summary",
            heading: `Errores del formulario (${uniqueErrors.length})`,
            label: `Ver los ${uniqueErrors.length} errores del formulario`,
        });

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = "error-summary-popup__close";
        closeButton.setAttribute("aria-label", "Cerrar aviso de errores");
        closeButton.textContent = "×";

        summary.append(message, allErrorsTooltip, closeButton);
        placeholder.replaceWith(summary);
        document.body.classList.add("error-summary-active");

        const header = document.getElementById("header");
        const updateStickyOffsets = () => {
            const headerHeight = header?.getBoundingClientRect().height || 0;
            const breadcrumbsHeight = breadcrumbs?.getBoundingClientRect().height || 0;
            document.documentElement.style.setProperty(
                "--admin-header-height",
                `${headerHeight}px`,
            );
            document.documentElement.style.setProperty(
                "--admin-breadcrumb-height",
                `${breadcrumbsHeight}px`,
            );
        };

        updateStickyOffsets();
        resizeHandler = updateStickyOffsets;
        window.addEventListener("resize", updateStickyOffsets);

        closeButton.addEventListener("click", () => {
            summary.remove();
            document.body.classList.remove("error-summary-active");
            window.removeEventListener("resize", updateStickyOffsets);
            resizeHandler = null;
        });
    }

    document.addEventListener("form-errors:refresh", initializeFormErrors);
    initializeFormErrors();
})();
