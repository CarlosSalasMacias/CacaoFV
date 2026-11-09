# Trazabilidad de la versión inicial

Fecha: 2026-11-09. Versión: 0.1.0.

Origen autorizado: paquete local de prueba del proyecto `instrumento_cacao_compartido/paquete_prueba`. Se copiaron `esquema.py`, `comun.py`, `analisis_doctoral.py`, `analisis_pregrado.py` y `configuracion.json`. Los originales se conservaron.

Cambios del motor: importador de Kobo; soporte de FUERA como categoría de respaldo sin asignar porcentajes; tratamiento de incertidumbre en inclusión del pago; fechas exactas opcionales sin fabricarlas, manteniendo controles sobre contradicciones; Monte Carlo de Pearson mediante tablas con márgenes fijos para compatibilidad con SciPy 1.14; identificación del piloto en informes. No se modificaron ponderaciones ni fórmulas de relativización.

La demostración copia 120 hogares enteramente ficticios del paquete original, semilla 20261105. Se conserva su identificación histórica SIM001… en el archivo interno de demostración; el formulario Kobo exige SIM_ para nuevas simulaciones. Los certificados de ejemplo son etiquetas simuladas. Ninguna cifra de esta base constituye evidencia sobre Fortaleza del Valle.

Bibliotecas web: Pyodide 0.29.3; dependencias del catálogo de esa distribución (SciPy 1.14.1 y statsmodels 0.14.4), openpyxl 3.1.5 instalado como paquete Python puro. Cada ejecución registra las versiones efectivamente utilizadas.

Fuentes técnicas primarias: https://pyodide.org/en/stable/usage/index.html y https://pyodide.org/en/stable/usage/webworker.html . Archivo de dependencias fijado: https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide-lock.json .

El adaptador trabaja con nombres XML. Aún debe contrastarse con un archivo descargado del proyecto real de Kobo; no se afirma haber realizado esa validación.
