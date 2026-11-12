# Guía de uso y alcance · v0.4

## Exportar desde Kobo

Descargue XLSX, con **nombres XML y valores XML** (no etiquetas de preguntas o respuestas). Incluya todas las hojas de grupos repetidos. Una fila principal es un hogar; las certificaciones y ventas son registros secundarios. No las convierta en hogares nuevos ni concatene las hojas manualmente.

Se admite el formulario compartido con periodo fijo **2025-11-01 a 2026-10-31**. Exporte PILOTO, CAMPO y SIMULACION por separado. Los identificadores vacíos o duplicados deben corregirse en el origen; la aplicación no elige automáticamente entre entrevistas duplicadas. Las simulaciones Kobo deben llevar prefijo SIM_.

La aplicación detiene el análisis ante errores de estructura, periodos mezclados, contradicciones importantes o repeticiones sin vínculo. Conserve el original. Revise los avisos, corrija en Kobo y vuelva a exportar.

## Doctorado

Comparación principal: **C1 estable, cobertura total y anual frente a C0 sin certificación durante el periodo**. C2 parcial, C3 transición y CU información insuficiente se describen por separado. Se requiere detalle de certificados para C1. Una cobertura declarada no equivale a una verificación documental; las fechas no conocidas permanecen vacías. No se inventan fechas exactas a partir de años.

Resultado primario: BF, beneficio familiar SAF, en **USD/hogar/año**.

BF = ventas cacao + otras ventas SAF + pago adicional no incluido en ventas − gastos operativos + autoconsumo valorado.

No se resta el trabajo familiar al BF. El indicador NI* sí incorpora su valoración. Las inversiones extraordinarias se mantienen separadas. No es una contabilidad completa de utilidad económica.

El análisis se inicia al seleccionar el Excel. La interfaz entrega descripciones y diferencias observadas para todas las bases de Kobo, incluido el piloto. Las respuestas de Kobo no documentan por sí solas el procedimiento de muestreo. La demostración ficticia permite comprobar las salidas inferenciales. El motor conserva la opción de analizar por separado una base con diseño aleatorio simple e independencia documentados.

El protocolo inferencial, cuando el diseño lo permite, contempla Welch bilateral e IC95% para diferencias de medias, ajuste de Holm para resultados secundarios, pruebas categóricas u ordinales y regresión con errores HC3 sujeta a los criterios del protocolo. Las salidas inferenciales de la demostración son ficticias.

Los nombres de esquemas se mantienen tal como fueron registrados; homogeneice variantes ortográficas en el origen antes de estudiar combinaciones. No trate distintos mercados de una misma norma como sellos independientes. Los resultados son asociaciones, sin identificación causal. Una p ≥ 0,05 no prueba equivalencia. Los umbrales del modelo no garantizan potencia.

## Pregrado

Se usan cinco indicadores económicos, cuatro ecológicos y seis sociales, definidos en el motor. El indicador opcional de agua está desactivado hasta validar su aplicabilidad.

Se aplica la relativización del Biograma de Sepúlveda et al. (2008), adaptada por Pachay Delgado (2024) a territorios cafeteros y ajustada aquí a los SAF con cacao. Los mínimos y máximos son comunes a todos los hogares elegibles, incluidos C2/C3/CU. Los indicadores constantes o sin datos se excluyen globalmente. Cada dimensión exige 80 % de cobertura de indicadores aplicables y la social exige además cuatro válidos. Solo la inaplicabilidad estructural en salud, escuela y decisiones reduce el denominador. [Biograma, capítulo II](https://eco.mdp.edu.ar/cendocu/repositorio/00661.pdf)

El índice global promedia las tres dimensiones con igual ponderación y requiere las tres calculables. La certificación no otorga puntos. Un valor de 1 significa posición relativa en esta muestra, no sostenibilidad absoluta. Cambiar los hogares importados puede cambiar mínimos, máximos e índices. Conserve la referencia de normalización para comparaciones posteriores.

## Gráficas

La pestaña Doctorado muestra la mediana y los percentiles 25 y 75 del beneficio familiar en C0 y C1. En Pregrado se abre el Biograma con las tres dimensiones. El selector de gráficas permite consultar también las telarañas de indicadores activos de cada dimensión y el gráfico de puntos que incluye el índice global. Los biogramas emplean la misma escala de 0 a 1 y muestran el número de hogares con datos válidos para cada eje. Una telaraña de detalle requiere al menos tres indicadores activos. Si a un grupo le falta un eje, se dibujan solo sus puntos disponibles.

Cada gráfica puede descargarse como PNG a 300 dpi o SVG editable. Ambos formatos se incluyen en el ZIP, junto con las tablas de las medias por dimensión e indicador.

## Resultados y privacidad

El ZIP contiene informes HTML, tablas CSV, indicadores por hogar, cobertura, referencias de relativización, avisos, metadatos, hash SHA-256 del archivo original y copia del código utilizado. Para Kobo, también incluye las hojas originales convertidas a CSV, conservando columnas y estados de las repeticiones. Guárdelo en un espacio privado. No publique ese ZIP ni los Excel reales en GitHub.

El motor descarga bibliotecas al iniciar, pero las respuestas se leen y analizan localmente. No usa la API de Kobo ni consume solicitudes de su análisis automático. Al recargar o cerrar la pestaña, se pierde la sesión; los archivos que usted haya descargado permanecen en su equipo.

## Validación pendiente

La base ficticia prueba el procedimiento, no la calidad del instrumento en campo. Antes de utilizar resultados en las tesis, pruebe un Excel exportado del proyecto real de Kobo, contraste algunos cálculos a mano, revise tiempos, faltantes y cobertura, y confirme el diseño de muestreo. Un instrumento y un script por sí solos no garantizan resultados defendibles.
