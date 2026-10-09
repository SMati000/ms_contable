(function () {
    "use strict";

    const SELECTOR_EMPRESA = "#id_empresa";
    const SELECTOR_CATEGORIA = "#id_categoria_laboral";

    function actualizarCategorias(empresaSelect) {
        const categoriaSelect = document.querySelector(SELECTOR_CATEGORIA);
        if (!categoriaSelect) return;

        const empresaId = empresaSelect.value;

        // Limpiar las categorías actuales
        categoriaSelect.innerHTML = "";

        if (!empresaId) {
            categoriaSelect.disabled = true;
            return;
        }

        categoriaSelect.disabled = true;

        // URL relativa al change_form actual:
        // /admin/empleados/agregar/ -> ../categorias-por-empresa/<id>/
        // /admin/empleados/<pk>/editar/ -> ../../categorias-por-empresa/<id>/
        const base = window.location.pathname.includes("/agregar/")
            ? "../categorias-por-empresa/"
            : "../../categorias-por-empresa/";

        fetch(base + empresaId + "/", {
            credentials: "same-origin",
        })
            .then((r) => {
                if (!r.ok) {
                    throw new Error("Error al obtener las categorías");
                }

                return r.json();
            })
            .then((data) => {
                // Opción vacía inicial
                categoriaSelect.add(
                    new Option("---------", "")
                );

                for (const categoria of data.categorias) {
                    categoriaSelect.add(
                        new Option(
                            categoria.nombre,
                            categoria.id
                        )
                    );
                }

                categoriaSelect.disabled = false;
            })
            .catch(() => {
                categoriaSelect.disabled = false;
            });
    }

    document.addEventListener("DOMContentLoaded", function () {
        const empresaSelect = document.querySelector(
            SELECTOR_EMPRESA
        );

        if (!empresaSelect) return;

        empresaSelect.addEventListener("change", function () {
            actualizarCategorias(this);
        });
    });
})();
