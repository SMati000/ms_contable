# Contrato de datos del recibo de sueldo

Este documento define la estructura de datos utilizada para generar el recibo de sueldo en SVG.

El objeto de datos es generado por `ReciboSueldoService` a partir de una `LiquidacionEmpleado` correspondiente a una liquidación cerrada.

La información utilizada para generar el recibo debe provenir de los datos históricos de la liquidación, de manera que el documento pueda regenerarse posteriormente sin depender de modificaciones realizadas sobre los datos actuales de la empresa, empleado o conceptos.

## Estructura general

```python
{
    "empresa": {...},
    "mes": int,
    "anio": int,
    "empleado": {...},
    "contribuciones": [...],
    "remunerativos": [...],
    "no_remunerativos": [...],
    "descuentos": [...],
    "costo_total_empleador": Decimal,
    "subtotal_contribuciones": Decimal,
    "sueldo_bruto": Decimal,
    "total_remunerativo": Decimal,
    "total_no_remunerativo": Decimal,
    "total_descuentos": Decimal,
    "sueldo_neto": Decimal,
    "neto_en_letras": str,
    "observaciones": str,
    "detalle": {...},
    "grafico_torta_svg": str | None,
}
```

## Empresa

```python
"empresa": {
    "nombre": str,
    "domicilio": str,
    "cuit": str,
}
```

Los datos corresponden a la empresa asociada a la liquidación. El domicilio utilizado debe ser el almacenado como parte de la liquidación y no el domicilio actual de la empresa.

## Empleado

```python
"empleado": {
    "apellido_nombre": str,
    "legajo": int,
    "sueldo_bruto": Decimal,
    "antiguedad": str,
    "fecha_ingreso": date,
    "categoria": str,
    "cuil": str,
    "banco": str,
    "periodo_pago": str,
}
```

La categoría y el banco corresponden a los valores registrados como parte de `LiquidacionEmpleado`.

La antigüedad se obtiene a partir de la fecha de ingreso y la fecha de pago de la liquidación. No se almacena como un dato independiente.

## Detalle de conceptos

Los conceptos se agrupan según su tipo de liquidación.

### Remunerativos

```python
"remunerativos": [
    {
        "concepto": str,
        "unidad": str,
        "base": Decimal,
        "unidades": Decimal,
        "monto": Decimal,
    },
]
```

### No remunerativos

```python
"no_remunerativos": [
    {
        "concepto": str,
        "unidad": str,
        "base": Decimal,
        "unidades": Decimal,
        "monto": Decimal,
    },
]
```

### Descuentos

```python
"descuentos": [
    {
        "concepto": str,
        "unidad": str,
        "base": Decimal,
        "unidades": Decimal,
        "monto": Decimal,
    },
]
```

### Contribuciones

```python
"contribuciones": [
    {
        "concepto": str,
        "unidad": str,
        "base": Decimal,
        "unidades": Decimal,
        "monto": Decimal,
    },
]
```

En todos los casos:

* `concepto` corresponde a la denominación de la `VersionConcepto` utilizada en la liquidación.
* `unidad` identifica si el concepto se expresa como cantidad o porcentaje.
* `unidades` corresponde al valor ingresado para el concepto.
* `base` es el resultado de evaluar `formula_base`.
* `monto` es el importe liquidado.
* `formula_base` no forma parte del contrato con la plantilla, ya que constituye un dato interno del mecanismo de cálculo.

## Totales

```python
"costo_total_empleador": Decimal,
"subtotal_contribuciones": Decimal,
"sueldo_bruto": Decimal,
"total_remunerativo": Decimal,
"total_no_remunerativo": Decimal,
"total_descuentos": Decimal,
"sueldo_neto": Decimal,
```

Los totales corresponden a los valores calculados y almacenados en `LiquidacionEmpleado`.

En particular:

* `sueldo_bruto` representa la remuneración bruta.
* `sueldo_neto` representa el importe a percibir por el trabajador.
* `subtotal_contribuciones` representa las contribuciones a cargo del empleador.
* `costo_total_empleador` representa el costo laboral total correspondiente al empleado.

## Composición del costo laboral

El recibo incluye un detalle de la composición del costo laboral del empleador.

La composición se obtiene agrupando las contribuciones de los conceptos liquidados según el `GrupoConcepto` asociado a cada `VersionConcepto`.

```python
"detalle": {
    "<codigo_grupo>": {
        "denominacion": str,
        "total": Decimal,
        "empleador": Decimal,
        "trabajador": Decimal,
    },
}
```

Los grupos corresponden al catálogo global de `GrupoConcepto`.

El sistema contempla, como mínimo, los grupos establecidos para la composición requerida por la normativa vigente:

* Sindical
* Seguridad social
* Obra social
* INSSJP
* ART
* SCVO
* Otros

Cada grupo puede contener conceptos correspondientes tanto al trabajador como al empleador.

### Significado de los importes

* `trabajador`: suma de los importes del grupo que son retenidos al trabajador.
* `empleador`: suma de los importes del grupo que representan un costo a cargo del empleador.
* `total`: suma de ambos importes.

Para la representación de la **composición del costo laboral del empleador**, se utiliza el importe `empleador` de cada grupo.

La remuneración bruta constituye también un componente del costo laboral del empleador. Por lo tanto, para la representación gráfica del costo total se considera:

```text
Costo laboral total
    = Remuneración bruta
    + Contribuciones a cargo del empleador
```

Los conceptos descontados al trabajador no incrementan el costo laboral del empleador y, por lo tanto, no forman parte de la composición utilizada para el gráfico de costo laboral.

## Gráfico de composición

El campo:

```python
"grafico_torta_svg": str | None
```

contiene un gráfico de torta generado como SVG.

El gráfico representa la composición del costo laboral total del empleador utilizando:

* la remuneración bruta;
* el importe a cargo del empleador correspondiente a cada `GrupoConcepto`.

El gráfico es generado por `GraficoCostoLaboralService`.

Este servicio recibe los datos ya calculados por `ReciboSueldoService` y no consulta directamente la base de datos.

La separación es:

```text
ReciboSueldoService
  ├── obtiene datos históricos y prepara el recibo
  └── detalle + remuneración bruta
              │
              ▼
  GraficoCostoLaboralService ──► SVG del gráfico
              │                         │
              └─────────┬───────────────┘
                        ▼
            ReciboSueldoSvgRenderer
                        │
                        ▼
                   recibo SVG
                  ┌─────┴──────────────┐
                  ▼                    ▼
             visor HTML              CairoSVG
        zoom, arrastre y lupa         svg2pdf
          ├── imprimir                 │
          ▼                            ▼
     diálogo del navegador       descarga PDF vectorial
```

`ReciboSueldoSvgRenderer` genera el recibo vectorial a partir del contrato de datos. El HTML lo muestra en un visor con zoom, desplazamiento, lupa y controles para imprimir o descargar el PDF. La descarga directa convierte el SVG a PDF con `CairoSVG.svg2pdf`; Pillow no interviene y el contenido gráfico conserva su representación vectorial. El botón de impresión usa el diálogo del navegador.

Los elementos de datos del SVG incluyen el atributo `data-variable` y un título emergente para identificar qué valor del contrato se representa.

El SVG se considera contenido confiable porque es generado internamente por el sistema y no proviene directamente de datos ingresados por el usuario.

## Importes expresados en letras

```python
"neto_en_letras": str
```

Representa el sueldo neto expresado en palabras.

Por ejemplo:

```text
SON PESOS QUINIENTOS MIL CON 00/100
```

El valor se genera a partir de `sueldo_neto` y no se almacena como información independiente.

## Observaciones

```python
"observaciones": str
```

Contiene observaciones adicionales que deban mostrarse en el recibo.

El campo puede estar vacío.

## Criterio de generación

El contrato de datos tiene como objetivo desacoplar la presentación del recibo de los modelos de dominio.

El servicio de presentación:

* no realiza cálculos de liquidación;
* no consulta la base de datos;
* no resuelve referencias entre conceptos;
* no determina grupos de conceptos;
* no calcula el costo laboral;
* no obtiene información de la empresa o del empleado.

Estas responsabilidades corresponden a los servicios de aplicación.

`ReciboSueldoSvgRenderer` recibe la información preparada y genera el SVG. La página HTML presenta el SVG y ofrece impresión desde el navegador o conversión directa a PDF mediante CairoSVG.
