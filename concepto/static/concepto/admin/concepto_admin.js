document.addEventListener("DOMContentLoaded", function () {
    const tipo = document.getElementById("id_tipo");
    const autoSeleccionar = document.getElementById(
        "id_auto_seleccionar_bases"
    );

    const bases = document.querySelectorAll(
        'input[name="bases_imponibles"]'
    );

    if (!tipo || !autoSeleccionar) {
        return;
    }

    const basesPorTipo = {
        remunerativo: ["2", "3", "4", "5", "6", "9", "10"],
        no_remunerativo: ["5", "9", "10"],
    };

    function actualizarBasesImponibles() {
        if (!autoSeleccionar.checked) {
            return;
        }

        const seleccionadas = basesPorTipo[tipo.value] || [];

        bases.forEach(function (base) {
            base.checked = seleccionadas.includes(base.value);
        });
    }

    tipo.addEventListener("change", actualizarBasesImponibles);
    autoSeleccionar.addEventListener("change", actualizarBasesImponibles);

    actualizarBasesImponibles();
});
