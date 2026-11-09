# CacaoFV

Aplicación estática para analizar la encuesta compartida de los sistemas agroforestales con cacao de Fortaleza del Valle. Dos salidas: bienestar socioeconómico familiar (doctorado) y sostenibilidad por relativización conjunta (pregrado).

## Uso

1. Abra la aplicación en GitHub Pages.
2. Pulse **Probar con 120 hogares ficticios**, o cargue un Excel de Kobo con nombres y valores XML y todas las hojas repetidas.
3. Indique el diseño de la muestra. Por defecto se entregan descripciones; el piloto siempre es descriptivo.
4. Examine las vistas Doctorado, Pregrado y Calidad y método. Descargue el ZIP con informes, tablas, datos normalizados, avisos y versiones.

Los datos del archivo se procesan en el navegador, mediante Python/WebAssembly en un worker. No se transmiten a un servidor de análisis ni se guardan en el repositorio. La aplicación descarga bibliotecas públicas desde jsDelivr/PyPI al iniciar: requiere internet y puede tardar unos minutos la primera vez. No almacena datos entre sesiones. Los ZIP descargados sí contienen datos y deben custodiarse localmente.

## Publicación en GitHub Pages

En el repositorio: **Settings → Pages → Build and deployment → Deploy from a branch → main → / (root) → Save**. No requiere servidor, claves de Kobo ni cuentas de pago. Dirección prevista: `https://carlossalasmacias.github.io/CacaoFV/`.

## Desarrollo y verificación

Sirva esta carpeta por HTTP; abrir `index.html` como archivo local no permite cargar el worker.

```sh
python -m http.server 8766 --bind 127.0.0.1
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

El motor se encuentra en `engine/`, separado de la interfaz. Se adaptaron los scripts preparados para el proyecto, conservando su lógica y el diccionario. El adaptador reconoce rutas de grupos XML y vincula repeticiones con `_index`/`_parent_index`, solo dentro del mismo archivo. No adivina etiquetas traducidas ni mezcla periodos o etapas.

Consulte [la guía](docs/GUIA.md) y [la trazabilidad](docs/TRAZABILIDAD.md). La versión inicial necesita una exportación real del piloto para verificar las particularidades del archivo generado por su proyecto de Kobo. Los resultados ficticios prueban funcionamiento, no validez empírica ni potencia del estudio.
