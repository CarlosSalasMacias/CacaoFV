"""Diccionario común de captura. No modifica los datos del usuario."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def campo(codigo, pregunta, etiqueta, unidad, tipo="numero", opciones=None, minimo=None, maximo=None):
    return dict(codigo=codigo, pregunta=pregunta, etiqueta=etiqueta, unidad=unidad,
                tipo=tipo, opciones=opciones, minimo=minimo, maximo=maximo)

CAMPOS = [
    campo("id_hogar", "Control", "Código anónimo único", "código", "texto"),
    campo("fecha", "Control", "Fecha de entrevista AAAA-MM-DD", "fecha", "texto"),
    campo("encuestador", "Control", "Código del encuestador", "código", "texto"),
    campo("comunidad", "Control", "Comunidad", "nombre", "texto"),
    campo("consiente", "Control", "Acepta participar en ambas tesis", "sí/no", "entero", [0,1]),
    campo("autoriza_registros", "Control", "Autoriza contrastar registros", "sí/no", "entero", [0,1]),
    campo("saf_confirmado", "Control", "Sistema agroforestal confirmado", "sí/no", "entero", [0,1]),
    campo("duracion_min", "Control", "Duración sin pausas", "minutos", minimo=0),
    campo("edad_inf", "Q1", "Edad del informante adulto", "años", "entero", minimo=18),
    campo("genero_inf", "Q1", "Género autodeclarado voluntario", "categoría", "texto"),
    campo("educ_inf", "Q1", "Nivel educativo", "categoría", "texto", ["NINGUNA","PRIMARIA","SECUNDARIA","TECNICA","UNIVERSITARIA"]),
    campo("n_hogar", "Q2", "Miembros habituales del hogar", "personas", "entero", minimo=1),
    campo("n_trab_fam", "Q2", "Miembros que trabajan en el SAF", "personas", "entero", minimo=0),
    campo("area_total_ha", "Q3", "Superficie total gestionada", "ha", minimo=0),
    campo("area_saf_ha", "Q3", "Superficie única del SAF encuestado", "ha", minimo=0.000001),
    campo("exp_cacao_anios", "Q3", "Experiencia en cacao", "años", minimo=0),
    campo("edad_cacao_anios", "Q3", "Edad predominante del cacaotal", "años", minimo=0),
    campo("tenencia", "Q3", "Tenencia principal", "categoría", "texto", ["PROPIA","ARRENDADA","PRESTADA","COMUNAL","OTRA"]),
    campo("tipo_cacao", "Q3", "Cacao predominante", "categoría", "texto", ["NACIONAL","CCN51","MIXTO","OTRO"]),
    campo("grupo_cert", "Q4", "Clasificación comprobada del periodo completo", "categoría", "texto", ["C0","C1","C2","C3","CU"]),
    campo("vc_usd", "Q5", "Dinero recibido por cacao en todos los canales", "USD/hogar/año", minimo=0),
    campo("canal_principal", "Q5", "Principal comprador", "categoría", "texto", ["FORTALEZA","OTRO","AMBOS"]),
    campo("vo_alim_usd", "Q6", "Ventas de otros alimentos del SAF", "USD/hogar/año", minimo=0),
    campo("vo_otro_usd", "Q6", "Ventas de madera leña y otros", "USD/hogar/año", minimo=0),
    campo("ac_alim_usd", "Q6", "Autoconsumo alimentario valorado", "USD/hogar/año", minimo=0),
    campo("ac_otro_usd", "Q6", "Autoconsumo de leña madera y otros", "USD/hogar/año", minimo=0),
    campo("productos_q6", "Q6", "Productos y base de anualización o valoración", "texto", "texto"),
    campo("cc_ins_usd", "Q7", "Gasto operativo en insumos consumibles", "USD/hogar/año", minimo=0),
    campo("cc_moc_usd", "Q7", "Trabajo contratado fuera del hogar", "USD/hogar/año", minimo=0),
    campo("cc_trans_usd", "Q7", "Transporte y comercialización", "USD/hogar/año", minimo=0),
    campo("cc_cert_usd", "Q7", "Cuotas y gastos de certificación del hogar", "USD/hogar/año", minimo=0),
    campo("cc_otros_usd", "Q7", "Otros gastos operativos atribuibles al SAF", "USD/hogar/año", minimo=0),
    campo("inversion_usd", "Q7", "Inversión extraordinaria separada de gastos", "USD/periodo", minimo=0),
    campo("kext_usd", "Q7", "Pago externo en productos excluido de autoconsumo", "USD/hogar/año", minimo=0),
    campo("dias_fam_decl", "Q8", "Días persona sumados de toda la familia", "días persona/año", minimo=0),
    campo("horas_dia_fam", "Q8", "Horas de cada día declarado", "horas/día", minimo=0.01, maximo=24),
    campo("base_trabajo", "Q8", "Componentes de reconstrucción del trabajo", "texto", "texto"),
    campo("jornal_decl_usd", "Q9", "Pago por jornal local comparable", "USD/jornada local", minimo=0),
    campo("horas_jornal", "Q9", "Horas del jornal local", "horas/jornada", minimo=0.01, maximo=24),
    campo("jornal_comida", "Q9", "El jornal incluye alimentación", "sí/no", "entero", [0,1]),
    campo("cubre_gastos_decl", "Q10", "El dinero cubrió gastos según informante", "sí/no", "entero", [0,1]),
    campo("o_negocio_usd", "Q11", "Ingreso NETO de otros cultivos animales negocios", "USD/hogar/año"),
    campo("o_trab_usd", "Q11", "Ingresos de trabajo fuera del SAF", "USD/hogar/año", minimo=0),
    campo("o_transf_usd", "Q11", "Bonos pensiones remesas y transferencias", "USD/hogar/año", minimo=0),
    campo("pm_cat_decl", "Q11", "Respaldo categórico si no hay montos externos", "categoría", "texto", ["MENOS25","25A49","50A74","75OMAS","FUERA"]),
    campo("registro_econ", "Q12", "0 no registra 1 parcial 2 habitual ambos", "categoría ordinal", "entero", [0,1,2]),
    campo("apoyo_aplicado", "Q13", "0 no recibió 1 recibió sin aplicar 2 aplicó", "categoría ordinal", "entero", [0,1,2]),
    campo("apoyo_ejemplo", "Q13", "Proveedor y recomendación aplicada", "texto", "texto"),
    campo("pago_cert_decl_usd", "Q14", "Pago adicional recibido por certificación", "USD/hogar/año", minimo=0),
    campo("pago_inclusion", "Q14", "Ya incluido en ventas SI NO PARCIAL o NS", "categoría", "texto", ["SI","NO","PARCIAL","NS"]),
    campo("pago_incluido_usd", "Q14", "Parte ya incluida solo si PARCIAL", "USD/hogar/año", minimo=0),
]
for cod,lab in [("precio","Mejor precio"),("comprador","Comprador estable"),("tecnico","Apoyo técnico"),("comunitario","Beneficio comunitario"),("otro","Otro beneficio"),("ninguno","Ningún beneficio")]:
    CAMPOS.append(campo("benef_"+cod,"Q15",lab+" priorizado","sí/no","entero",[0,1]))
for cod,lab in [("gasto","Gastos"),("tramite","Tiempo y trámites"),("manejo","Requisitos de manejo"),("otra","Otra dificultad"),("ninguna","Ninguna dificultad")]:
    CAMPOS.append(campo("dific_"+cod,"Q15",lab+" priorizada","sí/no","entero",[0,1]))
CAMPOS += [campo("barrera_cert","Q16","Principal barrera para no certificarse","categoría","texto",["ACCESO","COSTO","REQUISITOS","SIN_BENEFICIO","PROCESO","OTRA"])]
for i,lab in enumerate(["Cobertura del suelo","Abonos o reciclaje manejado","Control no químico","Otra protección de suelo sin duplicar cobertura"],1):
    CAMPOS.append(campo(f"pract_{i}","Q17",lab,"sí/no","entero",[0,1]))
CAMPOS += [
    campo("plag_sint","Q18","Usó plaguicidas de síntesis","sí/no","entero",[0,1]),
    campo("n_aplic_plag","Q18","Eventos de aplicación de plaguicidas","aplicaciones/año","entero",minimo=0),
    campo("producto_plag","Q18","Nombre de producto utilizado","texto","texto"),
    campo("fert_sint","Q18","Usó fertilizantes sintéticos","sí/no","entero",[0,1]),
    campo("conv_bosque","Q19","Convirtió bosque natural en últimos 3 años","sí/no","entero",[0,1]),
    campo("conv_bosque_ha","Q19","Área convertida en tres años","ha/3 años",minimo=0),
]
for i,lab in enumerate(["Vegetación junto a fuentes","Evita vertidos y lavado en fuentes","Control de riego"],1):
    CAMPOS += [campo(f"agua_aplica_{i}","Q20",lab+" es aplicable","sí/no","entero",[0,1]),campo(f"agua_{i}","Q20",lab+" se realiza","sí/no","entero",[0,1])]
CAMPOS += [
    campo("agua_otra","Q20","Otra práctica de protección de agua","texto","texto"),
    campo("arboles_especies_cat","Q21","0 ninguna 1 entre 1 y 2 2 entre 3 y 5 3 seis o más","clase de especies","entero",[0,1,2,3]),
    campo("arboles_ejemplos","Q21","Ejemplos presentes","texto","texto"),
    campo("alim_reduc_cat","Q22","0 nunca 1 en 1–2 meses 2 en 3–5 3 en 6 o más","categoría de meses","entero",[0,1,2,3]),
    campo("salud_acceso","Q23","0 nunca 1 algunas veces 2 siempre; NA no necesitó","categoría ordinal","entero",[0,1,2]),
    campo("escuela_asist","Q24","0 ninguno 1 algunos 2 todos; NA sin población","categoría ordinal","entero",[0,1,2]),
    campo("transp_dific","Q25","0 nunca 1 ocasional 2 frecuente","categoría ordinal","entero",[0,1,2]),
    campo("decision_part","Q26","0 nadie 1 algunos 2 todos; NA solo un adulto","categoría ordinal","entero",[0,1,2]),
    campo("satisf_saf","Q27","Satisfacción de 1 nada a 5 muy satisfecho","categoría ordinal","entero",[1,2,3,4,5]),
    campo("prioridad_texto","Q28","Principal cambio deseado","texto","texto"),
    campo("fuente_economica","Control","Fuente general de los montos; excepciones en Estados","categoría","texto",["REGISTRO","ESTIMACION","MIXTA"]),
    campo("observaciones","Control","Observaciones y discrepancias pendientes","texto","texto"),
]
CODIGOS = [x["codigo"] for x in CAMPOS]
INDICE = {x["codigo"]:x for x in CAMPOS}
CERT_COLS = ["id_hogar","esquema_id","norma_alcance","inicio","fin","area_ha","cubre_periodo_completo","fuente"]
VENTAS_COLS = ["id_hogar","operacion_id","presentacion","cantidad_original","unidad_original","kg_por_unidad","importe_usd","fuente"]
ESTADOS_COLS = ["id_hogar","campo","estado","fuente","nota"]

CONFIG = {
    "version":"1.0", "seed":20261105, "diseno":"aleatorio_simple_independiente",
    "alpha":0.05, "bootstrap_replicas":5000,
    "modelo_min_n":40, "modelo_min_grupo":15,
    "pregrado":{"min_cobertura":0.8,"social_min_validos":4,
                "pesos_dimensiones":{"economica":1/3,"ecologica":1/3,"social":1/3},
                "incluir_agua":False},
}

if __name__ == "__main__":
    (ROOT/"diccionario.json").write_text(json.dumps(CAMPOS,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"configuracion.json").write_text(json.dumps(CONFIG,ensure_ascii=False,indent=2),encoding="utf-8")
