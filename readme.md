# MS Contable - Liquidación de Sueldos

Sistema para la gestión y liquidación de sueldos de empresas y la generación de documentación asociada, desarrollado como una aplicación local.

## Descripción

El sistema permite administrar la información necesaria para realizar liquidaciones de sueldos y generar los documentos correspondientes.

Ver [imágenes ilustrativas](./docs/imgs_ilustrativas/).

Entre sus principales funcionalidades se encuentran:

* Gestión de empresas.
* Gestión de empleados y categorías laborales.
* Gestión de conceptos de liquidación.
* Gestión de plantillas de liquidación.
* Generación y cálculo de liquidaciones de sueldos.
* Generación de recibos de sueldo en formato PDF.
* Generación de archivos TXT compatibles con el sistema Libro de Sueldos Digital de ARCA.
* Conservación de la información histórica necesaria para reproducir liquidaciones y documentos generados.

El sistema está orientado a su utilización por parte de un contador para la gestión de las liquidaciones de una o más empresas.

## Alcance

El sistema contempla la gestión de empresas, empleados, conceptos de liquidación, categorías laborales y plantillas, así como la realización de liquidaciones y la generación de sus documentos asociados.

Las liquidaciones cerradas son inmutables y conservan la información necesaria para reproducir sus resultados independientemente de modificaciones posteriores en los datos maestros.

Los conceptos de liquidación y datos del empleado utilizan un esquema de versionado para conservar las versiones utilizadas en liquidaciones históricas.

## Fuera de alcance

El proyecto no contempla:

* Liquidación para trabajadores eventuales (registro 05 del txt de LSD de Arca)

* Integración automática con ARCA.
* Presentación automática del Libro de Sueldos Digital.

* Auditoría y trazabilidad integral de las operaciones.

* Uso simultáneo por múltiples usuarios.
* Acceso remoto o funcionamiento como servicio en línea.
* Autenticación y autorización de usuarios.

## Requisitos

Para ejecutar el proyecto se requiere Docker.

## Instalación

Ver el artefacto de instalación y uso en el [release](https://github.com/SMati000/ms_contable/releases) de la version que desea instalar.

## Lint

Activá el entorno virtual de Python del proyecto (en PowerShell, `.\.venv\Scripts\Activate.ps1`) e instalá las dependencias y herramientas de lint para Python/Django, HTML y CSS:

```bash
python -m pip install -r requirements-dev.txt
npm install
```

Ejecutá todos los chequeos con un solo comando:

```bash
npm run lint
```

## Documentación

Toda la documentación se encuentra dentro del directorio [docs](./docs/):

- Ver [modelo UML del dominio](./docs/dominio/modelo_dominio.md).
- Ver [modelo UML de casos de uso](./docs/casos_de_uso/00_modelo_uml.md) y sus definiciones adjuntas.
- Ver [modelo UML del DER](./docs/dominio/der.md).
- Ver [estructura del proyecto](./docs/specs_internas/estructura-py.md).

## Flujo general

A grandes rasgos, el funcionamiento del sistema sigue el siguiente flujo:

```text
Empresa
   │
   ├────────────── Categorías
   │                   ↓
   ├── Empleados ── Versiones │
   │                          │ ───
   └── Conceptos ── Versiones │    │
                                   │
                                   ▼
                            Generar liquidación
                                   │
                                   ▼
                            Liquidar empleados → Recibo PDF
                                   │
                                   ▼
                            Cerrar liquidación → TXT LSD
```

## Conformidad con Normativa Legal y Sistemas Externos

Ver: 
- [Documentacion sobre el dominio del sistema](./docs/dominio/readme.md)
- [Documentacion sobre la conformidad con regulaciones y sistemas externos](./docs/specs_externas)

## Tecnologías

* Django, Python
* DB Relacional, SQLite (pensado para uso local)
* HTML, CSS y JavaScript
