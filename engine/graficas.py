"""Figuras descriptivas basadas en las mismas tablas que se exportan a CSV."""
from base64 import b64encode
from pathlib import Path

import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from redaccion import valido

GRUPOS = {'C0': ('Sin certificación (C0)', '#515963', 'o'),
          'C1': ('Certificación estable (C1)', '#214c74', 'D')}
DIMENSIONES = {'economica': 'Económica', 'ecologica': 'Ecológica',
               'social': 'Social', 'IS': 'Índice global'}


def lienzo(titulo, etapa, nota):
    fig = Figure(figsize=(7.0, 4.0), facecolor='white')
    FigureCanvasAgg(fig)
    marca = {'SIMULACION': 'Simulación ficticia', 'PILOTO': 'Piloto descriptivo'}.get(etapa, 'Datos de campo')
    fig.text(.04, .93, titulo, fontsize=13, fontweight='bold', color='#19232e')
    fig.text(.04, .865, marca, fontsize=9, color='#515963')
    fig.text(.04, .065, nota, fontsize=9, color='#515963', linespacing=1.35)
    return fig


def configurar_ejes(ax, decimales):
    ax.set_axisbelow(True)
    ax.grid(axis='x', linewidth=.6, color='#e0e4e8')
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#8c949d')
    ax.tick_params(axis='y', length=0, pad=7)
    ax.tick_params(axis='x', length=3, color='#8c949d')
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda x, _: f'{x:,.{decimales}f}'.replace(',', ' ').replace('.', ',')
    ))


def beneficio(resumen, etapa):
    filas = {f['grupo']: f for f in resumen if f['grupo'] in GRUPOS and f['variable'] == 'bf_usd'
             and f['n'] > 0 and all(valido(f[k]) for k in ('p25', 'mediana', 'p75'))}
    if not filas:
        return None
    fig = lienzo('Beneficio familiar anual del SAF', etapa,
                 'Punto: mediana. Línea: percentiles 25 a 75.\nn = hogares con beneficio familiar calculable.')
    ax = fig.add_axes([.37, .28, .58, .50])
    etiquetas = []
    for y, (grupo, (nombre, color, marcador)) in enumerate(GRUPOS.items()):
        f = filas.get(grupo)
        etiquetas.append(f'{nombre}\n(n = {f["n"] if f else 0})')
        if f:
            ax.hlines(y, f['p25'], f['p75'], color=color, linewidth=2)
            ax.plot(f['mediana'], y, color=color, marker=marcador, markersize=6)
    ax.set_yticks([0, 1], etiquetas)
    ax.set_ylim(1.6, -.6)
    ax.set_xlabel('USD por hogar al año')
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, min_n_ticks=3))
    configurar_ejes(ax, 0)
    return fig


def sostenibilidad(resumen, etapa):
    filas = {(f['grupo'], f['indice']): f for f in resumen
             if f['grupo'] in GRUPOS and f['indice'] in DIMENSIONES and f['n'] > 0 and valido(f['media'])}
    if not filas:
        return None
    fig = lienzo('Sostenibilidad por grupo de certificación', etapa,
                 'Puntos: medias por grupo en una escala relativa de 0 a 1.\nn = hogares con puntuación calculable para cada medida.')
    ax = fig.add_axes([.20, .28, .58, .49])
    ax.set_xlim(0, 1)
    ax.set_ylim(3.5, -.5)
    ax.set_xticks([0, .2, .4, .6, .8, 1])
    ax.set_yticks(range(len(DIMENSIONES)), list(DIMENSIONES.values()))
    ax.set_xlabel('Puntuación media')
    for i, (grupo, (nombre, color, marcador)) in enumerate(GRUPOS.items()):
        offset = -.15 if i == 0 else .15
        for y, dimension in enumerate(DIMENSIONES):
            f = filas.get((grupo, dimension))
            if f:
                ax.plot(f['media'], y + offset, color=color, marker=marcador, markersize=5.5)
            ax.text(1.08, y + offset, f'{grupo}  n = {f["n"] if f else 0}',
                    transform=ax.get_yaxis_transform(), va='center', fontsize=9, color=color)
        ax.plot([], [], color=color, marker=marcador, linestyle='none', label=nombre)
    ax.legend(loc='lower left', bbox_to_anchor=(-.01, 1.00), ncol=2, frameon=False,
              borderaxespad=0, handletextpad=.25, columnspacing=1.0, fontsize=8.5)
    configurar_ejes(ax, 1)
    return fig


def generar_graficas(raiz, etapa, resumen_doctoral, resumen_pregrado):
    """Guarda SVG editable y PNG de 300 dpi. Envía los mismos archivos a la interfaz."""
    graficas = {}
    with mpl.rc_context({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none',
                         'svg.hashsalt': 'cacaofv'}):
        especificaciones = (
            ('doctoral', 'beneficio_familiar', 'Mediana y rango intercuartílico del beneficio familiar en C0 y C1.',
             beneficio, resumen_doctoral),
            ('pregrado', 'sostenibilidad', 'Medias de las tres dimensiones y del índice global en C0 y C1.',
             sostenibilidad, resumen_pregrado),
        )
        for tesis, nombre, alt, dibujar, resumen in especificaciones:
            fig = dibujar(resumen, etapa)
            if fig is None:
                continue
            salida = Path(raiz) / tesis / 'graficas'
            salida.mkdir(parents=True, exist_ok=True)
            png, svg = salida / (nombre + '.png'), salida / (nombre + '.svg')
            fig.savefig(png, dpi=300)
            fig.savefig(svg, metadata={'Date': None})
            graficas[tesis] = {'nombre': nombre, 'alt': alt, 'png': b64encode(png.read_bytes()).decode('ascii'),
                               'svg': svg.read_text(encoding='utf-8')}
            fig.clear()
    return graficas
