from decimal import Decimal

from concepto.choices import Categoria, Tipo, Unidad


GRUPOS = (
    ("sindical", "Sindical"),
    ("seguridad_social", "Seguridad Social"),
    ("obra_social", "Obra Social"),
    ("inssjp", "INSSJP"),
    ("art", "ART"),
    ("scvo", "SCVO"),
    ("entidades_empresariales", "Cámaras o Entidades Empresariales"),
)

BASES = (
    ("remuneracion_total", "Remuneración Total", "Remuneración bruta.", False),
    ("remuneracion_1", "Remuneración 1", "Base de aportes previsionales.", True),
    ("remuneracion_2", "Remuneración 2", "Base previsional e INSSJP.", True),
    ("remuneracion_3", "Remuneración 3", "Base FNE y asignaciones familiares.", True),
    ("remuneracion_4", "Remuneración 4", "Base de obra social y FSR.", True),
    ("remuneracion_5", "Remuneración 5", "Base de aportes INSSJP.", True),
    ("remuneracion_6", "Remuneración 6", "Base de aportes diferenciales.", True),
    ("remuneracion_7", "Remuneración 7", "Base de regímenes especiales.", True),
    ("remuneracion_8", "Remuneración 8", "Base de contribuciones de obra social.", True),
    ("remuneracion_9", "Remuneración 9", "Base de riesgos del trabajo.", True),
    ("remuneracion_10", "Remuneración 10", "Remuneración 2 menos detracciones.", False),
    ("detracciones", "Detracciones", "Monto a detraer de contribuciones.", False),
)

BASES_RENUMERATIVAS = tuple(f"remuneracion_{numero}" for numero in range(1, 10))

CONCEPTOS = (
    ("Sueldo básico", Categoria.TRABAJADOR, Tipo.REMUNERATIVO, Unidad.CANTIDAD, None, BASES_RENUMERATIVAS, "1", "850000"),
    ("Antigüedad", Categoria.TRABAJADOR, Tipo.REMUNERATIVO, Unidad.PORCENTAJE, None, BASES_RENUMERATIVAS, "5", "850000"),
    ("Presentismo", Categoria.TRABAJADOR, Tipo.REMUNERATIVO, Unidad.PORCENTAJE, None, BASES_RENUMERATIVAS, "8", "850000"),
    ("Horas extra", Categoria.TRABAJADOR, Tipo.REMUNERATIVO, Unidad.CANTIDAD, None, BASES_RENUMERATIVAS, "5", "2500"),
    ("Viáticos", Categoria.TRABAJADOR, Tipo.NO_REMUNERATIVO, Unidad.CANTIDAD, None, (), "1", "35000"),
    ("Jubilación", Categoria.TRABAJADOR, Tipo.DESCUENTO, Unidad.PORCENTAJE, "seguridad_social", (), "11", "850000"),
    ("INSSJP", Categoria.TRABAJADOR, Tipo.DESCUENTO, Unidad.PORCENTAJE, "inssjp", (), "3", "850000"),
    ("Obra social", Categoria.TRABAJADOR, Tipo.DESCUENTO, Unidad.PORCENTAJE, "obra_social", (), "3", "850000"),
    ("Cuota sindical", Categoria.TRABAJADOR, Tipo.DESCUENTO, Unidad.PORCENTAJE, "sindical", (), "2", "850000"),
    ("Contribución seguridad social", Categoria.EMPLEADOR, Tipo.CONTRIBUCION, Unidad.PORCENTAJE, "seguridad_social", (), "18", "850000"),
    ("ART", Categoria.EMPLEADOR, Tipo.CONTRIBUCION, Unidad.PORCENTAJE, "art", (), "3", "850000"),
    ("Seguro de vida obligatorio", Categoria.EMPLEADOR, Tipo.CONTRIBUCION, Unidad.CANTIDAD, "scvo", (), "1", "3500"),
    ("Aporte entidad empresarial", Categoria.EMPLEADOR, Tipo.CONTRIBUCION, Unidad.PORCENTAJE, "entidades_empresariales", (), "0.5", "850000"),
)

EMPLEADOS = (
    ("Sofía", "Pereyra"),
    ("Tomás", "Benítez"),
    ("Valentina", "Acosta"),
    ("Mateo", "Ferreyra"),
    ("Camila", "Roldán"),
    ("Joaquín", "Molina"),
    ("Martina", "Quiroga"),
    ("Lautaro", "Sosa"),
    ("Lucía", "Navarro"),
    ("Bruno", "Aguirre"),
)

EMPRESAS = ("Norte", "Sur", "Centro", "Litoral", "Cuyo", "Patagonia", "Pampa")
