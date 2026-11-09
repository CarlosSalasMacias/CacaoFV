# Verificación de la versión 0.1.0

Fecha: 2026-11-09.

Se ejecutaron diez pruebas automatizadas satisfactorias: rutas de columnas, repeticiones, preservación de ceros y NA, vínculos huérfanos, periodos/etapas/conteos incompatibles, C1 contradictorio, cobertura anual sin fabricar fechas, relativización con indicadores constantes, ejecución completa de simulación y bloqueo de inferencia en piloto.

Se verificó en el navegador local: carga de Pyodide y bibliotecas, cálculo de los dos análisis con 120 hogares ficticios, vistas doctoral y pregrado y descarga efectiva del ZIP. BF primario: 39 C0 y 71 C1 con datos; diferencia simulada C1−C0 = 1702,884112 USD/hogar/año, coincidente con el motor ejecutado localmente. IS calculable: 115 hogares. Estas cifras solo sirven como referencias de regresión del software.

La prueba de importación usa tablas que reproducen nombres y vínculos de una exportación Kobo; no procede de la cuenta real. No se ha verificado aún la lectura de un XLSX exportado por ese proyecto. Es necesaria esa comprobación durante el piloto, además de contrastar cálculos y revisar el diseño de muestreo.

El catálogo WebAssembly utiliza SciPy 1.14.1; se verificó la ejecución del Monte Carlo con márgenes fijos, que sustituye la interfaz más reciente de SciPy conservando el procedimiento estadístico. La semilla queda fijada; distintas implementaciones del muestreo Monte Carlo pueden diferir dentro de su error de simulación.
