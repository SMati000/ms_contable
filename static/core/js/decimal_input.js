(function () {
    "use strict";

    function sanitize(value) {
        // Treat comma and period as decimal separators.
        value = value.replace(/,/g, ".");

        // Keep a minus sign only when it is the first character.
        const negative = value.startsWith("-");
        value = value.replace(/-/g, "");

        // Remove everything except digits and decimal separators.
        value = value.replace(/[^\d.]/g, "");

        // Keep only the first decimal separator.
        const separator = value.indexOf(".");
        if (separator !== -1) {
            value =
                value.slice(0, separator + 1) +
                value.slice(separator + 1).replace(/\./g, "");

            // Keep one normalized decimal separator.
            const integerPart = value.slice(0, separator);
            const decimalPart = value.slice(separator + 1);

            value = integerPart + "." + decimalPart;
        }

        return (negative ? "-" : "") + value;
    }

    document.addEventListener("input", function (event) {
        const input = event.target;

        if (!input.matches(".decimal-input")) {
            return;
        }

        const maxDecimals = Number(input.dataset.decimalPlaces ?? 5);
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const original = input.value;

        // Sanitize the value and the text preceding each cursor position.
        const cleaned = sanitize(original);
        const newStart = sanitize(original.slice(0, start)).length;
        const newEnd = sanitize(original.slice(0, end)).length;
        const separator = cleaned.indexOf(".");
        const fractionalDigits = separator === -1
            ? 0
            : cleaned.length - separator - 1;

        input.setCustomValidity(
            fractionalDigits > maxDecimals
                ? `Usá como máximo ${maxDecimals} decimales.`
                : ""
        );

        if (cleaned !== original) {
            input.value = cleaned;
            input.setSelectionRange(
                Math.min(newStart, cleaned.length),
                Math.min(newEnd, cleaned.length)
            );
        }
    });
})();
