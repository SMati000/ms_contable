# Contrato temporal de pruebas Playwright

Actualizado: 2026-10-18 UTC. Registro separado del contrato de implementación.

## Estados

- `[x]` Ejecutado y confirmado con evidencia observable.
- `[~]` Ejecutado parcialmente o con alcance limitado.
- `[?]` No confirmado.
- `[U]` Requiere verificación del usuario.

## Entorno y seguridad

- Navegador: Chrome, sesión `MSContable`, tamaño normal existente.
- Servidor local: `127.0.0.1:8000`, autenticado como `admin` con las credenciales provistas.
- Base usada por el servidor: `tmp/playwright-verification-20261017.sqlite3`, confirmada en `tmp/playwright_settings.py` y mediante `DJANGO_SETTINGS_MODULE=tmp.playwright_settings`.
- Base original: `data/db.sqlite3`; no se aplicaron migraciones ni se enviaron escrituras a esa base. Su marca de modificación permaneció en `2026-10-17 22:13:07 -03:00` durante esta pasada.
- Liquidación y datos sintéticos de prueba se crearon en la copia descartable. El TXT no se subió a ARCA.

## Plan ejecutado por etapas

| Etapa | Estado | Evidencia / resultado |
|---|---|---|
| 0. Preflight y aislamiento | `[x]` | Configuración del servidor, ruta de la base clonada y separación de la base original verificadas. |
| 1. Autenticación, navegación y formularios admin | `[x]` | Login y panel confirmados; listas de liquidaciones, empleados, conceptos y plantillas cargaron. En el repaso final, alta de liquidación, lista de conceptos, alta de plantilla, edición de empleado y recibo respondieron HTTP 200. Un alta inválida permaneció en el formulario con error de campo, sin crear el objeto ni devolver 500. |
| 2. Precisión editable | `[x]` | El campo de unidades declara escala 5. `1,23456` se normalizó a `1.23456` y quedó válido; `1,234567` quedó inválido con mensaje de máximo 5 decimales. |
| 3. Cálculo complejo | `[x]` | En liquidación sintética se ejecutó el cálculo desde admin. La interfaz confirmó éxito y la copia conservó `123.45678` en detalle, base, resultado y neto; la pantalla presentó importes a 2 decimales. |
| 4. Recibo SVG/PDF y composición | `[U]` | Recibo original y duplicado disponibles; se inspeccionó visualmente el SVG/PDF, incluidos importes, unidades y neto en letras. No se observó recorte en la muestra; falta aceptación visual del usuario. |
| 5. TXT LSD | `[x]` | Descarga 200, `text/plain; charset=windows-1252`; decodificación CP1252 conservó acentos. Incluyó registros 01/02/03/04/06 con longitudes 35/115/51/370/93; el importe quedó a 2 decimales con redondeo `ROUND_HALF_UP`. Registro 05 no se genera por decisión de dominio documentada. |
| 6. Consola, respuestas y logs | `[x]` | La pasada final mostró 0 errores y 0 advertencias de consola. Los 404 observados correspondieron a rutas de prueba inexistentes. Durante diagnóstico se corrigieron un `NameError` en admin de empleado, un error JavaScript en lista de conceptos y una falla inicial de estáticos del entorno aislado (se reconstruyó `STATIC_ROOT` de la copia); sus páginas respondieron luego 200. |
| 7. Cierre y evidencia | `[x]` | Resultado documentado aquí y en `docs/contrato_temporal_mejoras.md`; la suite Django pasó 97 pruebas tras la reorganización final. |

## Limitaciones y seguimiento

- La pasada cubre recorridos prioritarios y complejos, no todas las combinaciones de formularios, permisos o datos históricos.
- La inspección visual del recibo requiere confirmación del usuario (`[U]`).
- No se verificó el envío del TXT ante ARCA ni la base real del usuario.
- Cálculos y exportaciones se verificaron con datos sintéticos en la copia, no con liquidaciones productivas.
- El servidor local de la copia se detendrá al cerrar la verificación; no se cambió ni limpió ningún archivo de datos o artefacto ajeno a esta tarea.
