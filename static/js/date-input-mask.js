(() => {
    const sourceSelector = 'input[type="text"].vDateField:not([data-date-segments-source])';
    const fieldNames = ["día", "mes", "año"];

    function parseDate(value) {
        const match = value.trim().match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
        if (match) return [match[1], match[2], match[3]];

        const isoMatch = value.trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (isoMatch) return [isoMatch[3], isoMatch[2], isoMatch[1]];
        return ["", "", ""];
    }

    function isValidPart(index, value) {
        if (!/^\d*$/.test(value) || value.length > (index === 2 ? 4 : 2)) return false;
        if (!value) return true;
        if (value.length === 1) return true;
        const number = Number(value);
        if (index === 0) return number >= 1 && number <= 31;
        if (index === 1) return number >= 1 && number <= 12;
        return value.length < 4 || (number >= 1 && number <= 9999);
    }

    function padPart(index, value) {
        return index < 2 && value.length === 1 ? `0${value}` : value;
    }

    function buildSourceValue(parts) {
        if (parts.every((part) => part === "")) return "";
        return parts.map((part, index) => padPart(index, part)).join("/");
    }

    function fillFromSource(source, fields) {
        const parts = parseDate(source.value);
        fields.forEach((field, index) => {
            field.value = parts[index];
            field.dataset.lastValid = field.value;
        });
    }

    function syncSource(source, fields) {
        source.value = buildSourceValue(fields.map((field) => field.value));
    }

    function nextField(field) {
        const fields = Array.from(field.closest(".date-input-segments").querySelectorAll(".date-input-segments__part"));
        const next = fields[fields.indexOf(field) + 1];
        if (next) next.focus();
    }

    function setParts(fields, parts) {
        if (!parts.every((part, index) => isValidPart(index, part))) return false;
        fields.forEach((field, index) => {
            field.value = parts[index];
            field.dataset.lastValid = field.value;
        });
        syncSource(fields[0].closest(".date-input-segments").querySelector("[data-date-segments-source]"), fields);
        return true;
    }

    function setupDateField(source) {
        if (source.dataset.dateSegmentsSource !== undefined || !source.parentNode) return;

        const wrapper = document.createElement("span");
        wrapper.className = "date-input-segments";
        const control = document.createElement("span");
        control.className = "date-input-segments__control";
        const initialParts = parseDate(source.value);
        const fields = [];

        fieldNames.forEach((name, index) => {
            const field = document.createElement("input");
            field.type = "text";
            field.inputMode = "numeric";
            field.autocomplete = "off";
            field.maxLength = index === 2 ? 4 : 2;
            field.className = `vTextField date-input-segments__part${index === 2 ? " date-input-segments__part--year" : ""}`;
            field.dataset.segmentIndex = String(index);
            field.value = initialParts[index];
            field.dataset.lastValid = field.value;
            field.setAttribute("aria-label", `${source.getAttribute("aria-label") || source.name || "Fecha"}: ${name}`);
            if (source.id) field.id = `${source.id}_${["dia", "mes", "anio"][index]}`;
            fields.push(field);
            control.appendChild(field);
            if (index < 2) {
                const separator = document.createElement("span");
                separator.className = "date-input-segments__separator";
                separator.setAttribute("aria-hidden", "true");
                separator.textContent = "/";
                separator.addEventListener("click", () => fields[index + 1].focus());
                control.appendChild(separator);
            }
        });

        wrapper.appendChild(control);
        source.dataset.dateSegmentsSource = "true";
        source.tabIndex = -1;
        source.setAttribute("aria-hidden", "true");
        source.removeAttribute("required");
        source.classList.add("date-input-segments__source");
        source.parentNode.insertBefore(wrapper, source);
        wrapper.appendChild(source);

        if (source.id) {
            document.querySelectorAll(`label[for="${CSS.escape(source.id)}"]`).forEach((label) => {
                label.htmlFor = fields[0].id;
            });
        }

        fields.forEach((field, index) => {
            field.addEventListener("input", () => {
                let value = field.value.replace(/\D/g, "").slice(0, field.maxLength);
                if (!isValidPart(index, value)) {
                    value = field.dataset.lastValid || "";
                    field.value = value;
                    field.setSelectionRange(value.length, value.length);
                    return;
                }
                field.value = value;
                field.dataset.lastValid = value;
                syncSource(source, fields);
            });

            field.addEventListener("keydown", (event) => {
                if (event.key === "Enter" && index < 2) {
                    event.preventDefault();
                    nextField(field);
                } else if (event.key === "/" && index < 2) {
                    event.preventDefault();
                    nextField(field);
                } else if (event.key === "ArrowRight" && index < 2 && field.selectionStart === field.value.length) {
                    nextField(field);
                } else if (event.key === "ArrowLeft" && index > 0 && field.selectionStart === 0) {
                    fields[index - 1].focus();
                }
            });

            field.addEventListener("blur", () => {
                field.value = padPart(index, field.value);
                if (!isValidPart(index, field.value)) field.value = "";
                field.dataset.lastValid = field.value;
                syncSource(source, fields);
            });

            field.addEventListener("paste", (event) => {
                const pasted = event.clipboardData?.getData("text")?.trim() || "";
                const fullDate = pasted.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
                const compactDate = pasted.match(/^(\d{2})(\d{2})(\d{4})$/);
                if (fullDate || compactDate) {
                    event.preventDefault();
                    const parts = fullDate ? fullDate.slice(1) : compactDate.slice(1);
                    if (setParts(fields, parts)) fields[2].focus();
                }
            });
        });

        source.addEventListener("change", () => fillFromSource(source, fields));
        source.addEventListener("focus", () => fillFromSource(source, fields));
        syncSource(source, fields);
    }

    function initialize(root = document) {
        root.querySelectorAll(sourceSelector).forEach(setupDateField);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => initialize());
    } else {
        initialize();
    }

    new MutationObserver((records) => {
        records.forEach((record) => record.addedNodes.forEach((node) => {
            if (node.nodeType !== Node.ELEMENT_NODE) return;
            if (node.matches?.(sourceSelector)) setupDateField(node);
            initialize(node);
        }));
    }).observe(document.documentElement, { childList: true, subtree: true });

    document.addEventListener("submit", (event) => {
        event.target.querySelectorAll(".date-input-segments").forEach((wrapper) => {
            const source = wrapper.querySelector("[data-date-segments-source]");
            const fields = Array.from(wrapper.querySelectorAll(".date-input-segments__part"));
            if (source && fields.length === 3) syncSource(source, fields);
        });
    }, true);
})();
