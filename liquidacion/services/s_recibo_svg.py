from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


class ReciboSueldoSvgRenderer:
    ancho = 794
    colores = {
        "tinta": "#4d5143",
        "amarillo": "#e3e899",
        "verde": "#d5d99f",
        "suave": "#f4f5e7",
        "fila": "#fbfbf6",
        "linea": "#858875",
        "subseccion": "#eef0d0",
    }
    columnas = (339, 105, 146, 148)

    def __init__(self, datos):
        self.datos = datos
        self.raiz = ET.Element(self._tag("svg"), {
            "id": "recibo-svg",
            "width": "210mm",
            "height": "297mm",
            "viewBox": "0 0 794 1123",
            "role": "img",
            "aria-label": "Recibo de haberes",
        })
        self.filas = self._calcular_alto_fila()

    def render(self):
        estilo = ET.SubElement(self.raiz, self._tag("style"))
        estilo.text = """
            text { font-family: Arial, Helvetica, sans-serif; fill: #20251b; }
            .empresa { font-size: 15px; font-weight: 700; }
            .titulo { font-size: 14px; font-weight: 700; letter-spacing: .45px; }
            .encabezado { font-size: 9.5px; font-weight: 700; letter-spacing: .3px; }
            .seccion { font-size: 8.4px; font-weight: 700; letter-spacing: .4px; }
            .barra { font-size: 10px; font-weight: 700; letter-spacing: .4px; }
            .importe { font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; }
            .numero { font-variant-numeric: tabular-nums; }
        """
        descripcion = ET.SubElement(self.raiz, self._tag("desc"))
        descripcion.text = (
            "Los datos variables están marcados con data-variable y un título emergente."
        )
        self._rect(0, 0, 794, 1123, "#fffef9")
        self._rect(22, 18, 750, 1087, "none", self.colores["tinta"], 1.2)
        self._dibujar_encabezado()
        y = self._dibujar_conceptos()
        self._dibujar_resumen(y)
        self._dibujar_pie(y)
        return ET.tostring(self.raiz, encoding="unicode")

    def _dibujar_encabezado(self):
        empresa = self.datos["empresa"]
        empleado = self.datos["empleado"]
        self._texto(32, 34, empresa["nombre"], 15, "bold", variable="empresa.nombre")
        self._texto(32, 51, empresa["domicilio"], 9, variable="empresa.domicilio")
        self._texto(
            32, 66, f"C.U.I.T.: {empresa['cuit']}", 9,
            variable="empresa.cuit",
        )
        self._rect(28, 77, 738, 29, self.colores["amarillo"], self.colores["linea"])
        self._texto(
            397, 91.5, "RECIBO DE HABERES  ·  LEY 20.744  ·  MENSUAL",
            14, "bold", "middle", clase="titulo",
        )

        self._fila_informacion(112, [
            (54, ["MES"], f"{self.datos['mes']:02d}", "mes"),
            (54, ["AÑO"], self.datos["anio"], "anio"),
            (207, ["APELLIDO Y NOMBRE"], empleado["apellido_nombre"], "empleado.apellido_nombre"),
            (105, ["N° LEGAJO"], empleado["legajo"], "empleado.legajo"),
            (148, ["SUELDO BRUTO"], f"$ {self._dinero(empleado['sueldo_bruto'])}", "empleado.sueldo_bruto"),
            (170, ["ANTIGÜEDAD", "RECONOCIDA"], empleado["antiguedad"], "empleado.antiguedad"),
        ])
        self._fila_informacion(156, [
            (108, ["FECHA DE INGRESO"], empleado["fecha_ingreso"], "empleado.fecha_ingreso"),
            (205, ["CATEGORÍA LABORAL"], empleado["categoria"], "empleado.categoria"),
            (100, ["C.U.I.L."], empleado["cuil"], "empleado.cuil"),
            (145, ["CARGAS SOCIALES", "/ BANCO"], empleado["banco"], "empleado.banco"),
            (180, ["FECHA DE PAGO"], empleado["periodo_pago"], "empleado.periodo_pago"),
        ])

    def _dibujar_conceptos(self):
        self._barra(214, "COSTO TOTAL EMPLEADOR", self.datos["costo_total_empleador"], "costo_total_empleador", 28)
        self._encabezado_tabla(247)
        y = self._filas_concepto(self.datos["contribuciones"], 269, "contribuciones")
        self._barra(y + 2, "SUBTOTAL CONTRIBUCIONES EMPLEADOR", self.datos["subtotal_contribuciones"], "subtotal_contribuciones", 23, pequena=True)
        self._barra(y + 30, "SUELDO BRUTO", self.datos["sueldo_bruto"], "sueldo_bruto", 26)
        self._encabezado_tabla(y + 57)
        y += 79

        for titulo, clave in (
            ("REMUNERATIVO", "remunerativos"),
            ("NO REMUNERATIVO", "no_remunerativos"),
            ("DESCUENTOS", "descuentos"),
        ):
            items = self.datos[clave]
            if not items:
                continue
            self._rect(28, y, 738, 17, self.colores["subseccion"], self.colores["linea"])
            self._texto(36, y + 8.5, titulo, 8.4, "bold", clase="seccion")
            y += 17
            y = self._filas_concepto(items, y, clave)
        return y

    def _dibujar_resumen(self, y):
        x0 = 28
        y0 = y + 7
        self._rect(x0, y0, 738, 43, self.colores["suave"], self.colores["linea"])
        tarjetas = (
            (188, "COMPOSICIÓN SALARIAL", "", None),
            (183, "REMUNERATIVO", f"$ {self._dinero(self.datos['total_remunerativo'])}", "total_remunerativo"),
            (183, "NO REMUNERATIVO", f"$ {self._dinero(self.datos['total_no_remunerativo'])}", "total_no_remunerativo"),
            (184, "DESCUENTOS", f"$ {self._dinero(self.datos['total_descuentos'])}", "total_descuentos"),
        )
        x = x0
        for ancho, etiqueta, valor, variable in tarjetas:
            self._rect(x, y0, ancho, 20, self.colores["verde"], self.colores["linea"])
            self._texto(x + ancho / 2, y0 + 10, etiqueta, 7.6, "bold", "middle")
            self._rect(x, y0 + 20, ancho, 23, "#ffffff", self.colores["linea"])
            self._texto(x + ancho / 2, y0 + 31.5, valor, 9.2, "bold", "middle", variable=variable)
            x += ancho

        neto_y = y0 + 49
        self._barra(neto_y, "SUELDO NETO", self.datos["sueldo_neto"], "sueldo_neto", 29)
        palabras_y = neto_y + 34
        self._rect(28, palabras_y, 738, 25, "#ffffff", self.colores["linea"])
        self._texto(37, palabras_y + 12.5, "SON PESOS:", 8.4, "bold", variable="etiqueta_neto_en_letras")
        self._texto(106, palabras_y + 12.5, self.datos["neto_en_letras"].upper(), 8.4, variable="neto_en_letras", maximo=650)

    def _dibujar_pie(self, y):
        tipo = self.datos.get("tipo", "original")
        observaciones = self.datos.get("observaciones") or "—"
        obs_y = y + 120
        self._rect(28, obs_y, 515, 53, "#ffffff", self.colores["linea"])
        self._texto(37, obs_y + 12, "OBSERVACIONES", 8, "bold", variable="etiqueta_observaciones")
        self._texto(37, obs_y + 27, observaciones, 8.4, variable="observaciones", maximo=490)
        texto_recibo = (
            "Recibí conforme copia del duplicado del presente recibo."
            if tipo == "duplicado"
            else "Recibí conforme copia del original del presente recibo."
        )
        self._texto(37, obs_y + 44, texto_recibo, 7.4, variable="tipo", maximo=490)
        self._rect(543, obs_y, 223, 53, "#ffffff", self.colores["linea"])
        self._linea(574, obs_y + 34, 736, obs_y + 34)
        firma = "Firma Trabajador" if tipo == "duplicado" else "Firma Empleador"
        self._texto(655, obs_y + 45, firma.upper(), 7.8, "bold", "middle", variable="tipo")

        titulo_y = y + 181
        self._rect(28, titulo_y, 738, 22, self.colores["amarillo"], self.colores["linea"])
        self._texto(397, titulo_y + 11, "DETALLE DE LA COMPOSICIÓN SALARIAL", 9.2, "bold", "middle", clase="seccion")
        body_y = titulo_y + 26
        self._rect(28, body_y, 488, 157, "#ffffff", self.colores["linea"])
        grupos = (
            ("sindical", "Sindical", "inssjp", "INSSJP"),
            ("seguridad_social", "Seguridad social", "art", "ART"),
            ("obra_social", "Obra social", "scvo", "SCVO"),
        )
        for indice, (izq, nombre_izq, der, nombre_der) in enumerate(grupos):
            yy = body_y + indice * 51
            self._composicion(28, yy, 232, izq, nombre_izq)
            self._composicion(276, yy, 240, der, nombre_der)
        nota = (
            "La seguridad social del empleador incluye SIPA, Fondo Nacional de Empleo "
            "y Asignaciones Familiares."
        )
        self._texto(29, body_y + 160, nota, 7.2, color="#555b4b", maximo=480)
        self._dibujar_grafico(body_y)

    def _composicion(self, x, y, ancho, clave, nombre):
        valores = self.datos["detalle"][clave]
        ancho_etiqueta = ancho * 0.69
        filas = (
            (f"Total {nombre}", valores["total"], True, "total"),
            ("Empleador", valores["empleador"], False, "empleador"),
            ("Trabajador", valores["trabajador"], False, "trabajador"),
        )
        for etiqueta, valor, total, campo in filas:
            alto = 17
            fondo = self.colores["subseccion"] if total else "#ffffff"
            self._celda(x, y, ancho_etiqueta, alto, etiqueta, fondo, 7.6 if total else 7.4, "start", 5, "bold" if total else "normal")
            self._celda(x + ancho_etiqueta, y, ancho - ancho_etiqueta, alto, f"$ {self._dinero(valor)}", fondo, 7.4, "end", 5, "bold" if total else "normal", f"detalle.{clave}.{campo}")
            y += alto

    def _dibujar_grafico(self, y):
        x, alto, ancho = 529, 179, 237
        self._rect(x, y, ancho, alto, "#ffffff", self.colores["linea"])
        self._rect(x, y, ancho, 21, self.colores["verde"], self.colores["linea"])
        self._texto(x + ancho / 2, y + 10.5, "COSTO TOTAL EMPLEADOR", 8.4, "bold", "middle")
        grafico_svg = self.datos.get("grafico_torta_svg")
        if not grafico_svg:
            self._texto(x + ancho / 2, y + 102, "No disponible", 9, "normal", "middle")
            return
        grafico = ET.fromstring(grafico_svg)
        grafico.set("x", str(x + 8))
        grafico.set("y", str(y + 25))
        grafico.set("width", str(ancho - 16))
        grafico.set("height", str(alto - 31))
        grafico.set("preserveAspectRatio", "xMidYMid meet")
        grafico.set("data-variable", "grafico_torta_svg")
        titulo = ET.Element(self._tag("title"))
        titulo.text = "Campo editable: grafico_torta_svg"
        grafico.insert(0, titulo)
        self.raiz.append(grafico)

    def _fila_informacion(self, y, celdas):
        x = 28
        for ancho, etiquetas, valor, variable in celdas:
            self._rect(x, y, ancho, 19, self.colores["verde"], self.colores["linea"])
            centro = y + 9.5
            desplazamiento = (len(etiquetas) - 1) * 4
            for indice, etiqueta in enumerate(etiquetas):
                self._texto(x + ancho / 2, centro - desplazamiento + indice * 8, etiqueta, 7.4, "bold", "middle")
            self._celda(x, y + 19, ancho, 25, valor, "#ffffff", 9.2, "middle", 5, "600", variable)
            x += ancho

    def _encabezado_tabla(self, y):
        for x, ancho, etiqueta in zip((28, 367, 472, 618), self.columnas, ("CONCEPTO", "UNIDAD", "BASE", "MONTO")):
            self._rect(x, y, ancho, 22, self.colores["verde"], self.colores["linea"])
            self._texto(x + ancho / 2, y + 11, etiqueta, 9.5, "bold", "middle", clase="encabezado")

    def _filas_concepto(self, items, y, prefijo):
        for indice, item in enumerate(items):
            fondo = "#ffffff" if indice % 2 == 0 else self.colores["fila"]
            valores = (
                (item.get("concepto", ""), "start", 7),
                ((item.get("unidad") or "").strip(), "middle", 0),
                (self._dinero(item.get("base")), "end", 0),
                (self._dinero(item.get("monto")), "end", 0),
            )
            x = 28
            for columna, ((valor, alineacion, _), ancho) in enumerate(zip(valores, self.columnas)):
                self._rect(x, y, ancho, self.filas, fondo, self.colores["linea"])
                margen = 7 if alineacion != "end" else 8
                tx = x + margen if alineacion == "start" else x + ancho - margen if alineacion == "end" else x + ancho / 2
                if columna in (2, 3) and valor:
                    valor = f"$ {valor}"
                variable = f"{prefijo}[{indice}].{('concepto', 'unidad', 'base', 'monto')[columna]}"
                self._texto(tx, y + self.filas / 2, valor, self._fuente_fila(), "normal", alineacion, variable=variable, maximo=ancho - margen * 2)
                x += ancho
            y += self.filas
        return y

    def _barra(self, y, etiqueta, importe, variable, alto, pequena=False):
        self._rect(28, y, 738, alto, self.colores["amarillo"], self.colores["linea"])
        tam = 9 if pequena else 10
        self._texto(37, y + alto / 2, etiqueta, tam, "bold", clase="seccion" if pequena else "barra")
        self._texto(756, y + alto / 2, f"$ {self._dinero(importe)}", 10 if pequena else 12, "bold", "end", variable=variable, clase="importe", maximo=210)

    def _celda(self, x, y, ancho, alto, valor, fondo, tam, alineacion="middle", margen=7, peso="normal", variable=None):
        self._rect(x, y, ancho, alto, fondo, self.colores["linea"])
        tx = x + margen if alineacion == "start" else x + ancho - margen if alineacion == "end" else x + ancho / 2
        self._texto(tx, y + alto / 2, valor, tam, peso, alineacion, variable=variable, maximo=ancho - margen * 2)

    def _texto(self, x, y, valor, tam=9, peso="normal", ancla="start", variable=None, clase=None, color=None, maximo=None):
        valor = "" if valor is None else str(valor)
        attrs = {
            "x": str(x),
            "y": str(y),
            "font-size": str(tam),
            "font-weight": str(peso),
            "text-anchor": ancla,
            "dominant-baseline": "middle",
        }
        if clase:
            attrs["class"] = clase
        if color:
            attrs["fill"] = color
        if valor and maximo and len(valor) * tam * 0.54 > maximo:
            attrs["font-size"] = str(round(maximo / (len(valor) * 0.54), 2))
        if variable:
            attrs["data-variable"] = variable
            attrs["aria-label"] = f"Dato editable: {variable}"
        elemento = ET.SubElement(self.raiz, self._tag("text"), attrs)
        elemento.text = valor
        if variable:
            titulo = ET.SubElement(elemento, self._tag("title"))
            titulo.text = f"Dato editable: {variable}"

    def _linea(self, x1, y1, x2, y2):
        ET.SubElement(self.raiz, self._tag("line"), {
            "x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2),
            "stroke": self.colores["linea"], "stroke-width": "0.9",
        })

    def _rect(self, x, y, ancho, alto, fondo, borde=None, grosor=0.7):
        attrs = {
            "x": str(x), "y": str(y), "width": str(ancho), "height": str(alto),
            "fill": fondo,
        }
        if borde:
            attrs.update({"stroke": borde, "stroke-width": str(grosor)})
        ET.SubElement(self.raiz, self._tag("rect"), attrs)

    def _calcular_alto_fila(self):
        secciones = sum(bool(self.datos[clave]) for clave in ("remunerativos", "no_remunerativos", "descuentos"))
        cantidad = len(self.datos["contribuciones"]) + sum(
            len(self.datos[clave])
            for clave in ("remunerativos", "no_remunerativos", "descuentos")
        )
        if not cantidad:
            return 18.5
        disponible = (1084 - 727 - secciones * 17) / cantidad
        return min(18.5, max(7, disponible))

    def _fuente_fila(self):
        return max(6.2, min(8.8, self.filas * 0.48))

    @staticmethod
    def _dinero(valor):
        if valor in (None, ""):
            return ""
        try:
            return f"{Decimal(str(valor)):,.2f}"
        except (InvalidOperation, ValueError):
            return str(valor)

    @staticmethod
    def _tag(nombre):
        return f"{{{SVG_NS}}}{nombre}"
