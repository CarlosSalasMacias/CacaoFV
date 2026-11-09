# Guía de uso y alcance · v0.1

## Exportar desde Kobo

Descargue XLSX, con **nombres XML y valores XML** (no etiquetas de preguntas o respuestas). Incluya todas las hojas de grupos repetidos. Una fila principal es un hogar; las certificaciones y ventas son registros secundarios. No las convierta en hogares nuevos ni concatene las hojas manualmente.

Se admite el formulario compartido con periodo fijo **2025-11-01 a 2026-10-31**. Exporte PILOTO, CAMPO y SIMULACION por separado. Los identificadores vacíos o duplicados deben corregirse en el origen; la aplicación no elige automáticamente entre entrevistas duplicadas. Las simulaciones Kobo deben llevar prefijo SIM_.

La aplicación detiene el análisis ante errores de estructura, periodos mezclados, contradicciones importantes o repeticiones sin vínculo. Conserve el original. Revise los avisos, corrija en Kobo y vuelva a exportar.

## Doctorado

Comparación principal: **C1 estable, cobertura total y anual frente a C0 sin certificación durante el periodo**. C2 parcial, C3 transición y CU información insuficiente se describen por separado. Se requiere detalle de certificados para C1. Una cobertura declarada no equivale a una verificación documental; las fechas no conocidas permanecen vacías. No se inventan fechas exactas a partir de años.

Resultado primario: BF, beneficio familiar SAF, en **USD/hogar/año**.

BF = ventas cacao + otras ventas SAF + pago adicional no incluido en ventas − gastos operativos + autoconsumo valorado.

No se resta el trabajo familiar al BF. El indicador NI* sí incorpora su valoración. Las inversiones extraordinarias se mantienen separadas. No es una contabilidad completa de utilidad económica.

El análisis inferencial se habilita únicamente al seleccionar **aleatorio simple, hogares independientes**. Si no corresponde, se entregan descripciones y diferencias observadas. Censo, conveniencia y diseños complejos no se fuerzan a un análisis inferencial simple. El piloto permanece descriptivo, cualquiera sea la selección.

Cuando corresponde: Welch bilateral e IC95% para diferencias de medias; Holm para familias de resultados secundarios; Fisher o Pearson para categorías, con Monte Carlo condicional de 19.999 réplicas en tablas RxC dispersas; Mann–Whitney para ordinales; regresión lineal con errores HC3 ajustando por logaritmo de superficie actual y miembros del hogar, sujeta a tamaño y rango suficientes. El ZIP incluye bootstrap complementario, diagnósticos y comparaciones exploratorias entre combinaciones de certificaciones.

Los nombres de esquemas se mantienen tal como fueron registrados; homogeneice variantes ortográficas en el origen antes de estudiar combinaciones. No trate distintos mercados de una misma norma como sellos independientes. Los resultados son asociaciones, sin identificación causal. Una p ≥ 0,05 no prueba equivalencia. Los umbrales del modelo no garantizan potencia.

## Pregrado

Se usan cinco indicadores económicos, cuatro ecológicos y seis sociales, definidos en el motor. El indicador opcional de agua está desactivado hasta validar su aplicabilidad.

Se relativiza con mínimos y máximos comunes a todos los hogares elegibles del archivo, incluidos C2/C3/CU, en el sentido favorable del indicador. Los indicadores constantes o sin datos se excluyen globalmente. Cada dimensión exige 80% de cobertura de indicadores aplicables; la social exige además cuatro válidos. Solo NA estructural en salud, escuela y decisiones reduce el denominador; NS/NR nunca lo hacen.

El índice global promedia las tres dimensiones con igual ponderación y requiere las tres calculables. La certificación no otorga puntos. Un valor de 1 significa posición relativa en esta muestra, no sostenibilidad absoluta. Cambiar los hogares importados puede cambiar mínimos, máximos e índices. Conserve la referencia de normalización para comparaciones posteriores.

## Resultados y privacidad

El ZIP contiene informes HTML, tablas CSV, indicadores por hogar, cobertura, referencias de relativización, avisos, metadatos, hash SHA-256 del archivo original y copia del código utilizado. Para Kobo, también incluye las hojas originales convertidas a CSV, conservando columnas y estados de las repeticiones. Guárdelo en un espacio privado. No publique ese ZIP ni los Excel reales en GitHub.

El motor descarga bibliotecas al iniciar, pero las respuestas se leen y analizan localmente. No usa la API de Kobo ni consume solicitudes de su análisis automático. Al recargar o cerrar la pestaña, se pierde la sesión; los archivos que usted haya descargado permanecen en su equipo.

## Validación pendiente

La base ficticia prueba el procedimiento, no la calidad del instrumento en campo. Antes de utilizar resultados en las tesis, pruebe un Excel exportado del proyecto real de Kobo, contraste algunos cálculos a mano, revise tiempos, faltantes y cobertura, y confirme el diseño de muestreo. Un instrumento y un script por sí solos no garantizan resultados defendibles.
