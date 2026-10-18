# Contrato temporal de mejoras

Actualizado: 2026-10-18 UTC. Registra el estado del árbol de trabajo; no implica commit ni despliegue.

## Estados

- `[x]` Implementado y verificado con evidencia indicada.
- `[~]` Parcial: queda una decisión, cobertura o aceptación pendiente.
- `[?]` Sin evidencia suficiente.
- `[U]` Requiere confirmación funcional o visual del usuario.

## Estado por área

| Área | Estado | Resultado y límite actual |
|---|---|---|
| Validaciones | `[~]` | Las reglas cubiertas se validan en modelos, formularios, servicios y registros LSD; las entradas inválidas conocidas producen errores de dominio/campo. No certifica una auditoría exhaustiva de todas las rutas ni la regla oficial para casos excepcionales del módulo 11 de CUIL/CUIT. |
| Decimales | `[x]` | Cálculos y campos de unidades, importes, bases y resultados acordados admiten y persisten hasta 5 decimales. Las salidas aplican la regla documentada abajo. |
| Fórmulas | `[x]` | Grafo, evaluación, validación y persistencia quedaron separados; errores previsibles son de dominio y el cálculo integrado conserva precisión y rollback. |
| Recibo | `[x]` | Importes visibles y en letras coinciden a 2 decimales; unidades muestran de 2 a 5 decimales significativos. Integración SVG/PDF verificada; falta la aceptación visual final del usuario. |
| TXT LSD | `[x]` | La revisión de carga anticipada, mapeo, validación, formato ANSI y exportación de los registros admitidos quedó cerrada. Registro 05 no se genera intencionalmente: trabajadores eventuales están fuera del dominio según `docs/adr/003_registro-05-txt-lsd.md`. |
| Formularios y admin | `[x]` | Se corrigieron errores de validación/renderizado detectados, se separaron responsabilidades y los archivos de código modificados cumplen el límite de 400 líneas, salvo migración histórica preexistente. |

## Contrato decimal vigente

| Contexto | Escala / regla |
|---|---|
| Cálculo y persistencia de unidades, detalles, bases y resultados | Hasta 5 decimales, según campo/modelo. |
| Entrada web en campos con escala 5 | Acepta hasta 5; una sexta cifra fraccionaria se marca inválida en cliente y servidor, sin truncamiento silencioso. |
| Recibo: importes | 2 decimales; cuantización `ROUND_HALF_EVEN`. |
| Recibo: unidades | Entre 2 y 5 decimales significativos; cuantización `ROUND_HALF_EVEN`. |
| Recibo: neto en letras | 2 decimales; el mismo `ROUND_HALF_EVEN` que el importe visible. |
| TXT LSD: campos decimales de los generadores | 2 decimales; `ROUND_HALF_UP`, cotejado con la planilla oficial. |

La salida LSD aplica anchos y límites propios de cada registro. El redondeo que excedería el rango del campo se rechaza. Se conservó sin cambios la regla funcional de fecha de pago que el usuario ya corrigió.

## Hecho y comprobado

- Los modelos validables ejecutan validación antes de guardar; las operaciones masivas revisadas prevalidan los objetos antes de escribir.
- Se endurecieron valores ausentes/mal formados en identificadores, CBU, relaciones opcionales, fechas, tipos y valores numéricos no finitos.
- Las fórmulas validan sintaxis, referencias, ciclos y resultados antes de persistir; se cubren dependencias, errores tipados y rollback.
- Los mappers LSD describen sus relaciones requeridas; `liquidacion/lsd/queries.py` prepara la consulta y los mappers no consultan la base por su cuenta.
- Validación y formato comunes se comparten entre registros; caracteres que no se representan en CP1252 producen un error controlado.
- La descarga LSD declara `windows-1252`; Registro 06 admite observación vacía y la rellena según la planilla oficial.
- Registro 05 conserva un generador probado unitariamente, pero no forma parte de la descarga: el dominio no representa trabajadores eventuales y el ADR decide excluirlos.
- La suite completa pasó 97 pruebas; `manage.py check` no detectó problemas; `makemigrations --check --dry-run` no encontró cambios pendientes; `git diff --check` terminó limpio (solo informó una advertencia LF/CRLF en `plantilla_liquidacion/tests.py`).

## Pendiente para cerrar la revisión global

- `[~]` Contrastar casos límite del algoritmo CUIL/CUIT con una fuente primaria oficial antes de certificar excepciones del módulo 11.
- `[U]` Confirmar visualmente el diseño final del recibo; se revisó en navegador y no se observaron recortes.
- `[?]` `SPR` no identifica ningún módulo o símbolo del repositorio. La sigla se tomó del mensaje anterior del usuario; falta que indique a qué flujo se refiere.
- Mantener fuera de alcance el soporte de trabajadores eventuales/Registro 05 hasta modelar esa modalidad; la decisión actual está revisada y documentada en el ADR.

## Criterio de cierre

La revisión global se cierra cuando no quedan reglas contables ambiguas dentro del alcance, las verificaciones automatizadas y de navegador están registradas y se reciben las confirmaciones `[U]`. Los resultados de la copia de prueba no equivalen a verificación sobre producción.
