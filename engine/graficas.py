"""Figuras descriptivas basadas en las mismas tablas que se exportan a CSV."""
from base64 import b64encode
from functools import partial
from math import cos, pi, sin
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
INDICADORES = {
    'economica': {'E1': 'Margen operativo', 'E2': 'Beneficio por persona',
                  'E3': 'Fuentes económicas', 'E4': 'Registro económico', 'E5': 'Apoyo técnico aplicado'},
    'ecologica': {'A1': 'Prácticas de manejo', 'A2': 'Menor frecuencia de plaguicidas',
                  'A3': 'Menor conversión de bosque', 'A4': 'Riqueza arbórea declarada', 'A5': 'Prácticas de agua'},
    'social': {'S1': 'Continuidad alimentaria', 'S2': 'Acceso a salud', 'S3': 'Asistencia escolar',
               'S4': 'Acceso a transporte', 'S5': 'Participación en decisiones', 'S6': 'Satisfacción con el SAF'},
}


def lienzo(titulo, etapa, nota, alto=4.0, posicion_nota=.065):
    fig = Figure(figsize=(7.0, alto), facecolor='white')
    FigureCanvasAgg(fig)
    marca = {'SIMULACION': 'Simulación ficticia', 'PILOTO': 'Piloto descriptivo'}.get(etapa, 'Datos de campo')
    fig.text(.04, .93, titulo, fontsize=13, fontweight='bold', color='#19232e')
    fig.text(.04, .865, marca, fontsize=9, color='#515963')
    fig.text(.04, posicion_nota, nota, fontsize=9, color='#515963', linespacing=1.35)
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


def telarana(resumen, etapa, ejes, titulo, *, general=False):
    filas = {(f['grupo'], f['indice']): f for f in resumen
             if f['grupo'] in GRUPOS and f['indice'] in ejes and f['n'] > 0 and valido(f['media'])}
    if len(ejes) < 3 or not filas:
        return None
    fig = lienzo(titulo, etapa,
                 'Cada eje muestra una media relativa de 0 a 1. n = hogares con datos válidos por eje.\n'
                 'Si falta una media, el grupo se representa con puntos en los ejes disponibles.',
                 alto=8.5 if general else 5.0, posicion_nota=.033 if general else .065)
    if general:
        ax = fig.add_axes([.07, .385, .86, .46], aspect='equal')
        ax.set(xlim=(-1.22, 1.22), ylim=(-1.22, 1.22))
        for i, (dimension, indicadores) in enumerate(INDICADORES.items()):
            izquierda = .04 + i*.325
            fig.text(izquierda, .325, DIMENSIONES[dimension], fontsize=9, fontweight='bold')
            visibles = [clave for clave in indicadores if clave in ejes]
            for j, clave in enumerate(visibles):
                y = .30 - j*.039
                fig.text(izquierda, y, f'{clave} {ejes[clave]}', fontsize=8, color='#19232e')
                fig.text(izquierda, y-.016, conteos(filas, clave), fontsize=8, color='#515963')
    else:
        ax = fig.add_axes([.06, .22, .88, .59], aspect='equal')
        ax.set(xlim=(-1.75, 1.75), ylim=(-1.34, 1.40))
    ax.set_axis_off()
    angulos = [pi/2 - 2*pi*i/len(ejes) for i in range(len(ejes))]
    radios = [(cos(a), sin(a)) for a in angulos]
    for nivel in (.25, .50, .75, 1):
        contorno = [(nivel*x, nivel*y) for x,y in radios]
        contorno.append(contorno[0])
        ax.plot(*zip(*contorno), color='#8c949d' if nivel == 1 else '#dfe4e8', linewidth=.75)
        ax.text(.035, nivel-.02, f'{nivel:g}'.replace('.', ','), color='#515963', fontsize=8,
                va='top', zorder=2.5)
    ax.text(.035, -.02, '0', color='#515963', fontsize=8, va='top')
    for (clave, nombre), (x,y) in zip(ejes.items(), radios):
        ax.plot([0,x], [0,y], color='#c8cfd6', linewidth=.7, zorder=1)
        alineacion = 'left' if x > .2 else 'right' if x < -.2 else 'center'
        etiqueta = clave if general else f'{nombre}\n{conteos(filas, clave)}'
        ax.text(1.11*x, 1.11*y, etiqueta, ha=alineacion,
                va='bottom' if y > .85 else 'top' if y < -.85 else 'center', fontsize=8.5, color='#19232e')
    for grupo, (nombre, color, marcador) in GRUPOS.items():
        puntos = []
        for clave, (x,y) in zip(ejes,radios):
            fila = filas.get((grupo,clave))
            if fila:
                puntos.append((x*fila['media'], y*fila['media']))
        if not puntos:
            continue
        completa = len(puntos) == len(ejes)
        if completa:
            puntos.append(puntos[0])
        ax.plot(*zip(*puntos), color=color, marker=marcador, markersize=4.5, linewidth=1.55,
                linestyle=('--' if grupo == 'C0' else '-') if completa else 'none', label=nombre, zorder=4)
    fig.legend(loc='lower center', bbox_to_anchor=(.5,.35 if general else .135), ncol=2, frameon=False, fontsize=9)
    return fig


def conteos(filas, clave):
    return ' · '.join(f'{grupo} n={filas.get((grupo, clave), {}).get("n", 0)}' for grupo in GRUPOS)


def generar_graficas(raiz, etapa, resumen_doctoral, resumen_pregrado, resumen_normalizados):
    """Guarda SVG editable y PNG de 300 dpi. Envía los mismos archivos a la interfaz."""
    graficas = {}
    with mpl.rc_context({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none',
                         'svg.hashsalt': 'cacaofv'}):
        dimensiones = {k: v for k,v in DIMENSIONES.items() if k != 'IS'}
        activos = {fila['indice'] for fila in resumen_normalizados}
        ejes_general = {clave: etiqueta for etiquetas in INDICADORES.values()
                        for clave, etiqueta in etiquetas.items() if clave in activos}
        especificaciones = [
            ('doctoral', 'beneficio_familiar', 'Beneficio familiar', 'Mediana y rango intercuartílico del beneficio familiar en C0 y C1.',
             partial(beneficio, resumen_doctoral, etapa)),
            ('pregrado', 'biograma_indicadores', 'Biograma general por indicadores',
             f'Telaraña con {len(ejes_general)} indicadores agrupados en las dimensiones económica, ecológica y social.',
             partial(telarana, resumen_normalizados, etapa, ejes_general, 'Biograma general de sostenibilidad', general=True)),
            ('pregrado', 'biograma_dimensiones', 'Resumen por dimensiones', 'Telaraña de medias de las dimensiones económica, ecológica y social.',
             partial(telarana, resumen_pregrado, etapa, dimensiones, 'Biograma de sostenibilidad por dimensiones')),
            ('pregrado', 'sostenibilidad', 'Dimensiones e índice global', 'Medias de las tres dimensiones y del índice global en C0 y C1.',
             partial(sostenibilidad, resumen_pregrado, etapa)),
        ]
        for dimension, etiquetas in INDICADORES.items():
            ejes = {clave: nombre for clave,nombre in etiquetas.items() if clave in activos}
            nombre = dimensiones[dimension].lower()
            titulo = f'Biograma de la dimensión {nombre}'
            especificaciones.append(('pregrado', f'biograma_{dimension}', f'Indicadores de la dimensión {nombre}',
                                    f'Telaraña de indicadores normalizados de la dimensión {nombre}.',
                                    partial(telarana, resumen_normalizados, etapa, ejes, titulo)))
        for tesis, nombre, titulo, alt, dibujar in especificaciones:
            fig = dibujar()
            if fig is None:
                continue
            salida = Path(raiz) / tesis / 'graficas'
            salida.mkdir(parents=True, exist_ok=True)
            png, svg = salida / (nombre + '.png'), salida / (nombre + '.svg')
            fig.savefig(png, dpi=300)
            fig.savefig(svg, metadata={'Date': None})
            graficas.setdefault(tesis, []).append({
                'nombre': nombre, 'titulo': titulo, 'alt': alt,
                'png': b64encode(png.read_bytes()).decode('ascii'), 'svg': svg.read_text(encoding='utf-8'),
            })
            fig.clear()
    return graficas
