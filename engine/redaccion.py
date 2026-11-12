"""Borradores reproducibles a partir de las tablas calculadas, sin servicios externos."""
import math

DISEÑOS = {
    'NO_DEFINIDO': 'Selección por conveniencia o diseño pendiente de confirmar',
    'aleatorio_simple_independiente': 'Muestreo aleatorio simple con hogares independientes',
    'censo': 'Censo del universo definido',
    'complejo': 'Diseño con estratos, conglomerados o ponderaciones',
}
TITULOS = {
    'doctoral': 'Bienestar socioeconómico de hogares productores de cacao',
    'pregrado': 'Sostenibilidad de sistemas agroforestales con cacao',
}
WELCH = "Welch, B. L. (1947). The generalization of ‘Student’s’ problem when several different population variances are involved. *Biometrika, 34*, 28–35. https://doi.org/10.1093/biomet/34.1-2.28"
HOLM = "Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*, 65–70. https://www.jstor.org/stable/4615733"
HC3 = "Long, J. S., y Ervin, L. H. (2000). Using heteroscedasticity consistent standard errors in the linear regression model. *The American Statistician, 54*, 217–224. https://doi.org/10.1080/00031305.2000.10474549"
SARANDON = "Sarandón, S. J., y Flores, C. C. (2009). Evaluación de la sustentabilidad en agroecosistemas: Una propuesta metodológica. *Agroecología, 4*, 19–28. https://revistas.um.es/agroecologia/article/view/117131"
PACHAY = "Pachay Delgado, L. E. (2024). *Sostenibilidad de territorios rurales cafeteros del cantón Santa Ana Manabí, Ecuador* [Tesis de maestría, Universidad Técnica de Manabí]."
SELLARE = "Sellare, J., Meemken, E.-M., Kouamé, C., y Qaim, M. (2020). Do sustainability standards benefit smallholder farmers also when accounting for cooperative effects? Evidence from Côte d’Ivoire. *American Journal of Agricultural Economics, 102*, 681–695. https://doi.org/10.1002/ajae.12015"
TENNHARDT = "Tennhardt, L. M., Lambin, E. F., Curran, M., y Schader, C. (2023). Implementation of sustainable farming practices by cocoa farmers in Ecuador and Uganda: The influence of value chain factors. *Frontiers in Sustainable Food Systems, 7*, 1167683. https://doi.org/10.3389/fsufs.2023.1167683"
NOMBRES = {
    'bf_usd': 'Beneficio familiar del SAF',
    'cfp_usd': 'Flujo de caja con prima adicional',
    'ac_usd': 'Autoconsumo valorado',
    'nip_usd': 'Ingreso con trabajo familiar valorado',
    'bf_persona_usd': 'Beneficio por persona',
    'bf_ha_usd': 'Beneficio por hectárea de SAF',
    'bf_jornal_usd': 'Beneficio por jornal familiar',
    'pm_pct': 'Participación monetaria del SAF',
    'cc_usd': 'Gastos operativos',
    'economica': 'Dimensión económica',
    'ecologica': 'Dimensión ecológica',
    'social': 'Dimensión social',
    'IS': 'Índice de sostenibilidad',
    'social_comun': 'Dimensión social con indicadores comunes',
    'IS_comun': 'Índice con dimensión social común',
}


def valido(valor):
    return isinstance(valor, (int, float)) and math.isfinite(valor)


def numero(valor, decimales=2):
    return f'{valor:.{decimales}f}'.replace('.', ',') if valido(valor) else '—'


def pvalor(valor):
    if not valido(valor):
        return '—'
    return '< 0,0001' if valor < 0.0001 else numero(valor, 4)


def referencias(*fuentes):
    return '## Referencias\n\n' + '\n\n'.join(fuentes)


def cabecera(tesis, apartado, resultado):
    marcas = {
        'SIMULACION': '**Simulación con hogares ficticios. Uso exclusivo de demostración.**',
        'PILOTO': '**Piloto. Borrador para revisar la aplicación del instrumento.**',
    }
    marca = marcas.get(resultado['etapa'], '**Borrador para revisión del equipo de investigación.**')
    return f'# {apartado}\n\n{TITULOS[tesis]} · Fortaleza del Valle\n\n{marca}\n\n'


def metodologia(tesis, r, meta, ejecucion):
    cfg = ejecucion['configuracion']
    versiones = ejecucion['versiones']
    inicio, fin = meta['periodo_inicio'], meta['periodo_fin']
    modalidad = DISEÑOS.get(r['diseno'], 'Diseño pendiente de confirmar')
    if r['etapa'] == 'SIMULACION' and r['diseno'] == 'aleatorio_simple_independiente':
        modalidad = 'Simulación con pruebas habilitadas para demostrar el análisis de hogares independientes'
    comun = f"""## Diseño, población y unidad de análisis

Se planteó una comparación observacional entre hogares productores vinculados a Fortaleza del Valle, Ecuador, con un sistema agroforestal (SAF) con cacao. La unidad de análisis fue el hogar productor. Las certificaciones y las ventas registradas en formularios repetidos se vincularon al hogar correspondiente. El periodo anual de referencia fue del {inicio} al {fin}.

La modalidad registrada para esta ejecución fue **{modalidad}**. Se incluyeron los registros con consentimiento para participar y SAF confirmado. El contraste principal comparó hogares sin certificación en el periodo (C0) y hogares con certificación estable que cubría todo el SAF durante el periodo (C1). Los hogares con cobertura parcial, transición o información insuficiente conservaron su clasificación y se describieron por separado.

## Instrumento y tratamiento de datos

Se utilizó un cuestionario estructurado en KoboToolbox. El identificador de hogar permitió comprobar duplicados y vincular registros repetidos. Los montos monetarios se expresaron en dólares estadounidenses. Se conservó el cero observado y se distinguieron las respuestas «no sabe», «no responde» y «no aplica». Cada estimación utilizó los datos válidos de la variable correspondiente.

"""
    if r['etapa'] == 'SIMULACION':
        comun = comun.replace('Se utilizó un cuestionario estructurado en KoboToolbox.', 'La ejecución se realizó con datos simulados para el cuestionario estructurado de KoboToolbox.')
    if r['etapa'] == 'PILOTO':
        comun += 'El piloto se procesó en modalidad descriptiva, con independencia de la opción seleccionada en la interfaz.\n\n'
    if tesis == 'doctoral':
        especifico = """## Variables y análisis doctoral

El resultado principal fue el beneficio familiar anual aportado por el SAF (USD/hogar/año). Se sumaron las ventas de cacao y otros productos del SAF, el autoconsumo valorado y la parte de la prima de certificación no incluida en las ventas. De ese total se restaron los costos operativos. La valoración del trabajo familiar se aplicó en un indicador separado. Cuando se conocía el monto de la prima pero se desconocía si estaba incluida en las ventas, se calcularon escenarios para los límites del beneficio familiar.

Se calcularon medias, desviaciones estándar, medianas, cuartiles y tamaños válidos por grupo para los resultados económicos, y frecuencias por categoría para las variables sociales y de gestión. La diferencia se definió como la media de C1 menos la media de C0.

La comparación se planteó a nivel de hogar. La afiliación organizativa y la certificación son características que pueden coincidir en el sector cacaotero, por lo que el contraste se interpreta en el contexto de la organización estudiada (Sellare et al., 2020).

"""
        fuentes = (SELLARE, WELCH, HOLM, HC3)
    else:
        pc = cfg['pregrado']
        pesos = ', '.join(f"{NOMBRES[k].lower()} {numero(v * 100)} %" for k, v in pc['pesos_dimensiones'].items())
        agua = 'Se incluyó el indicador de prácticas aplicables de agua.' if pc['incluir_agua'] else 'El indicador opcional de prácticas de agua quedó fuera del índice.'
        especifico = f"""## Indicadores y cálculo del índice

La evaluación mediante indicadores siguió el enfoque multidimensional de Sarandón y Flores (2009). Se adaptó a los SAF con cacao el procedimiento de relativización usado por Pachay Delgado (2024) en territorios cafeteros.

La dimensión económica reunió la proporción de flujo de caja respecto del ingreso bruto con prima adicional, el beneficio por persona, el número de fuentes económicas positivas, el registro económico y la aplicación de apoyo técnico. La dimensión ecológica reunió el número de prácticas de manejo, la frecuencia de aplicaciones de plaguicidas, la conversión de bosque y la categoría de riqueza de especies arbóreas declarada. La dimensión social reunió continuidad alimentaria, acceso a salud, asistencia escolar, transporte, participación en decisiones y satisfacción con el aporte del SAF. {agua}

Cada indicador se llevó a una escala de 0 a 1 con el mínimo (m) y máximo (M) observados entre los hogares elegibles de todos los grupos. Para indicadores de sentido favorable creciente se usó (x − m)/(M − m). Para los de sentido decreciente se usó (M − x)/(M − m). Se excluyeron del promedio los indicadores constantes o sin valores válidos. Las puntuaciones representan la posición relativa en la muestra de referencia.

Cada dimensión se calculó como el promedio de sus indicadores normalizados válidos, con una cobertura mínima del {numero(pc['min_cobertura'] * 100, 0)} % de los indicadores activos aplicables. La dimensión social requirió además al menos {pc['social_min_validos']} indicadores válidos. La inaplicabilidad estructural redujo el denominador en salud, escolaridad y participación en decisiones. Las respuestas desconocidas o ausentes mantuvieron el indicador en el denominador cuando era aplicable.

El índice global requirió las tres dimensiones y usó estas ponderaciones ({pesos}). Se examinó una variante de sensibilidad que restringe la dimensión social a los indicadores activos de continuidad alimentaria, transporte y satisfacción, con datos completos para ese conjunto. La condición de certificación se utilizó como variable de agrupación. Se resumieron las dimensiones y el índice por grupo y se calculó la diferencia de medias C1 menos C0.

"""
        fuentes = (SARANDON, PACHAY, WELCH, HOLM)
    if r['diseno'] == 'aleatorio_simple_independiente':
        especifico += 'La comparación de medias se realizó con la prueba bilateral de Welch e intervalos de confianza del 95 % (Welch, 1947). Se aplicó el ajuste de Holm a las familias de contrastes (Holm, 1979).\n\n'
        if tesis == 'doctoral':
            especifico += f"""El contraste primario de beneficio familiar se reportó por separado del ajuste de Holm aplicado a los indicadores económicos secundarios. Para variables ordinales se usó la prueba de Mann–Whitney con corrección por empates. Para variables categóricas se usó chi cuadrado de Pearson, la prueba exacta de Fisher en tablas 2 × 2 dispersas y una aproximación Monte Carlo condicional con 19 999 réplicas para otras tablas dispersas.

Se especificó una regresión lineal del beneficio familiar sobre certificación estable, logaritmo de la superficie del SAF y tamaño del hogar, con errores estándar robustos HC3 (Long y Ervin, 2000). El ajuste se habilitó con al menos {cfg['modelo_min_n']} observaciones completas y {cfg['modelo_min_grupo']} por grupo, además de rango completo. El análisis complementario contempló remuestreo bootstrap con {cfg['bootstrap_replicas']} réplicas para la diferencia de medias y de medianas cuando ambos grupos alcanzaron ocho observaciones válidas. Las comparaciones por combinaciones de sellos se trataron como exploratorias y quedaron sujetas al tamaño de los grupos.

"""
    else:
        especifico += 'Esta ejecución se limitó a descripciones por grupo y diferencias observadas entre medias.\n\n'
        fuentes = (SELLARE,) if tesis == 'doctoral' else (SARANDON, PACHAY)
    software = ', '.join(f'{k} {v}' for k, v in versiones.items())
    pendientes = """## Aspectos por completar antes de incorporar a la tesis

[Confirmar marco de productores, procedimiento real de selección y fechas de aplicación.]

[Completar protocolo de consentimiento, aprobación ética cuando corresponda y verificación documental de las certificaciones.]

"""
    bibliografia = referencias(*fuentes) if fuentes else ''
    return (cabecera(tesis, 'Metodología', r) + comun + especifico
            + f'Los cálculos se ejecutaron con CacaoFV {r["version"]} y {software}.\n\n'
            + pendientes + bibliografia).rstrip() + '\n'


def contraste(row, unidad):
    n0, n1 = row.get('n_C0', 0), row.get('n_C1', 0)
    diferencia = row.get('diferencia_C1_C0')
    if not valido(diferencia):
        return f'El contraste requirió observaciones válidas en ambos grupos (C0, n = {n0} y C1, n = {n1}).'
    cifras = (f'La media fue {numero(row["media_C0"])} en C0 (n = {n0}) y '
              f'{numero(row["media_C1"])} en C1 (n = {n1}). '
              f'La diferencia C1 − C0 fue {numero(diferencia)} {unidad}.')
    if all(valido(row.get(k)) for k in ('ic95_inf', 'ic95_sup', 'p')):
        cifras += f' El IC del 95 % abarcó de {numero(row["ic95_inf"])} a {numero(row["ic95_sup"])} y el valor p de Welch fue {pvalor(row["p"])}.'
        if valido(row.get('p_holm')):
            cifras += f' El valor p ajustado por Holm fue {pvalor(row["p_holm"])}.'
    else:
        cifras += ' La comparación de este indicador es descriptiva.'
    return cifras


def tabla_contrastes(filas):
    lineas = [
        '| Indicador | Unidad | n C0 | n C1 | Media C0 | Media C1 | C1 − C0 | IC 95 % sin ajuste | p | p Holm |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |',
    ]
    for f in filas:
        nombre = NOMBRES.get(f['variable'], f['variable'])
        ic = f'{numero(f["ic95_inf"])} a {numero(f["ic95_sup"])}' if valido(f.get('ic95_inf')) else '—'
        celdas = [nombre, f['unidad'], str(f['n_C0']), str(f['n_C1']), numero(f['media_C0']),
                  numero(f['media_C1']), numero(f['diferencia_C1_C0']), ic, pvalor(f['p']), pvalor(f['p_holm'])]
        lineas.append('| ' + ' | '.join(celdas) + ' |')
    return '\n'.join(lineas)


def resultados_discusion(tesis, r, comparaciones):
    grupos = ', '.join(f'{k} (n = {v})' for k, v in sorted(r['grupos'].items()))
    base = f'Se analizaron {r["n_analizados"]} hogares elegibles distribuidos en {grupos}.'
    clave = 'bf_usd' if tesis == 'doctoral' else 'IS'
    filas = r['economicos'] if tesis == 'doctoral' else comparaciones
    principal = next((f for f in filas if f['variable'] == clave), {})
    unidad = 'USD/hogar/año' if tesis == 'doctoral' else 'puntos en la escala de 0 a 1'
    texto = [cabecera(tesis, 'Resultados y discusión', r), '## Resultados', base,
             f'### {NOMBRES[clave]}', contraste(principal, unidad), tabla_contrastes(filas)]
    if tesis == 'doctoral':
        alimentacion = next((f for f in r['sociales'] if f['variable'] == 'alim_reduc_si'), {})
        if valido(alimentacion.get('diferencia_pp')):
            texto.append(
                'La diferencia C1 − C0 en la proporción de hogares que declararon haber reducido '
                f'la alimentación fue {numero(alimentacion["diferencia_pp"])} puntos porcentuales '
                f'(C0, n = {alimentacion["n_C0"]} y C1, n = {alimentacion["n_C1"]}).'
            )
        modelo = next((f for f in r['modelo'] if f['termino'] == 'cert_estable'), None)
        if modelo and valido(modelo.get('coeficiente')):
            texto.append(
                'En el modelo ajustado por superficie del SAF y tamaño del hogar, la diferencia asociada a C1 fue '
                f'{numero(modelo["coeficiente"])} USD/hogar/año '
                f'(IC del 95 % de {numero(modelo["ic95_inf"])} a {numero(modelo["ic95_sup"])}).'
            )
        discusion = ('El beneficio familiar integra ventas, autoconsumo, gastos operativos y primas adicionales. '
                     'La diferencia agregada requiere examinar esos componentes y sus denominadores para identificar cuáles contribuyen al contraste. '
                     'El estudio de Sellare et al. (2020) sobre cacao en Côte d’Ivoire muestra la pertinencia de considerar '
                     'el papel de las cooperativas al interpretar las asociaciones con certificación. En Fortaleza del Valle, '
                     'el ajuste por superficie y tamaño del hogar deja abierta la influencia de otras diferencias entre hogares y esquemas.')
        fuentes = (SELLARE,)
    else:
        validos = sum(f['n'] for f in r['sostenibilidad'] if f['indice'] == 'IS')
        texto.append(f'El índice global se pudo calcular para {validos} de los {r["n_analizados"]} hogares elegibles.')
        dimensiones = [f for f in filas if f['variable'] in ('economica', 'ecologica', 'social')
                       and valido(f['diferencia_C1_C0'])]
        if dimensiones:
            brechas = ', '.join(f'{NOMBRES[f["variable"]].lower()} {numero(f["diferencia_C1_C0"], 3)}'
                                for f in dimensiones)
            texto.append(f'Las diferencias de medias C1 − C0 por dimensión fueron {brechas}, en la escala de 0 a 1. Cada media se calculó con los hogares que tenían datos suficientes para esa dimensión.')
        sensibilidad = next((f for f in filas if f['variable'] == 'IS_comun'), {})
        if valido(sensibilidad.get('diferencia_C1_C0')):
            texto.append('Al usar los indicadores sociales comunes, la diferencia de medias fue '
                         f'{numero(sensibilidad["diferencia_C1_C0"], 3)} puntos '
                         f'(C0, n = {sensibilidad["n_C0"]} y C1, n = {sensibilidad["n_C1"]}). '
                         'Esta variante puede cambiar tanto los indicadores incluidos como los hogares con índice calculable.')
        discusion = ('La comparación describe el desempeño relativo respecto de los mínimos y máximos de los hogares analizados. '
                     'Las dimensiones deben interpretarse junto con la cobertura de sus indicadores. El índice con indicadores sociales '
                     'comunes permite examinar cuánto depende la comparación de la composición de esa dimensión. '
                     'Tennhardt et al. (2023) examinaron la relación entre factores de la cadena de valor y prácticas de manejo del cacao '
                     'en Ecuador y Uganda. Su trabajo orienta la revisión de diferencias en acceso a capacitación y apoyo técnico, '
                     'mientras que los puntajes de este estudio se interpretan dentro de su propia escala y población de referencia.')
        fuentes = (TENNHARDT,)
    texto.append('## Discusión')
    if r['etapa'] == 'SIMULACION':
        texto.append('Las cifras ilustran el funcionamiento del análisis con hogares ficticios. El contraste con la literatura queda pendiente de contar con datos de campo.')
    elif r['etapa'] == 'PILOTO':
        texto.append('La comparación del piloto sirve para revisar cobertura, variabilidad y consistencia de los indicadores. La discusión sustantiva se completará con el levantamiento definitivo.')
    else:
        dif = principal.get('diferencia_C1_C0')
        if valido(dif) and dif != 0:
            direccion = 'mayor' if dif > 0 else 'menor'
            texto.append(f'Entre los hogares con datos válidos, la media del indicador principal fue {direccion} en C1.')
        limites = (principal.get('ic95_inf'), principal.get('ic95_sup'))
        if all(valido(v) for v in limites) and limites[0] <= 0 <= limites[1]:
            texto.append('El intervalo del 95 % incluye el cero y admite diferencias en ambas direcciones cuando sus límites tienen signos opuestos. La precisión disponible limita la interpretación de la brecha.')
        texto.append(discusion)
        texto.append('Antes de generalizar la comparación, corresponde revisar el diseño de selección y la distribución de faltantes por grupo. El diseño observacional limita la atribución causal. La precisión se interpreta con el intervalo cuando se pudo calcular.')
        texto.append(referencias(*fuentes))
    return '\n\n'.join(parte.strip() for parte in texto) + '\n'


def generar_documentos(resultado, meta, ejecucion, comparaciones):
    return {
        tesis: {
            'metodologia': metodologia(tesis, resultado, meta, ejecucion),
            'resultados_discusion': resultados_discusion(tesis, resultado, comparaciones),
        }
        for tesis in TITULOS
    }
