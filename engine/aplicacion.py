"""Adaptador Kobo → tablas del protocolo. Se ejecuta en memoria local del navegador."""
from pathlib import Path
import json, re, hashlib, zipfile, io, shutil
import pandas as pd
from esquema import CODIGOS, CAMPOS, CERT_COLS, VENTAS_COLS, ESTADOS_COLS
from comun import ErrorDatos

VERSION = '0.2.0'
PERIODO = ('2025-11-01', '2026-10-31')

def texto(v):
    if v is None or pd.isna(v): return ''
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    return str(v).strip()

def columnas(tabla):
    """Reconoce rutas de grupos sin aceptar dos columnas con el mismo nombre final."""
    nombres = [re.split(r'[/\\]', str(c))[-1] for c in tabla.columns]
    if len(nombres) != len(set(nombres)):
        raise ErrorDatos('Hay columnas ambiguas con el mismo nombre final. Exporte nombres XML, sin etiquetas.')
    t = tabla.copy(); t.columns = nombres
    return t.fillna('').map(texto)

def fecha(v):
    return texto(v)[:10]

def adaptar_kobo(hojas):
    hojas = {n: columnas(t) for n,t in hojas.items()}
    principales = [t for t in hojas.values() if 'id_hogar' in t and 'consiente' in t]
    if len(principales) != 1:
        raise ErrorDatos('No se reconoce una única hoja principal. Descargue XLSX de Kobo con nombres y valores XML, e incluya todas las hojas.')
    principal = principales[0]
    if principal.empty: raise ErrorDatos('El archivo no contiene entrevistas.')
    for c in ['grupo_cert','tipo_levantamiento','periodo_inicio','periodo_fin','vc_usd','cc_ins_usd','salud_acceso_estado']:
        if c not in principal: raise ErrorDatos(f'Falta {c}. Revise la versión del formulario y la exportación XML.')
    etapas = set(principal.tipo_levantamiento) - {''}
    if len(etapas)!=1 or '' in set(principal.tipo_levantamiento):
        raise ErrorDatos('El archivo mezcla etapas o tiene etapas vacías. Exporte SIMULACION, PILOTO o CAMPO por separado.')
    etapa = next(iter(etapas))
    if etapa not in ('SIMULACION','PILOTO','CAMPO'): raise ErrorDatos('Tipo de levantamiento desconocido.')
    for c,esperado in zip(['periodo_inicio','periodo_fin'],PERIODO):
        if set(principal[c].map(fecha)) != {esperado}:
            raise ErrorDatos(f'{c}: se requiere el periodo común {PERIODO[0]} a {PERIODO[1]}. No mezcle periodos.')
    if etapa=='SIMULACION' and not principal.id_hogar.str.startswith('SIM_').all():
        raise ErrorDatos('En simulaciones Kobo todos los códigos deben comenzar por SIM_.')
    if etapa!='SIMULACION' and principal.id_hogar.str.startswith('SIM').any():
        raise ErrorDatos('Hay códigos de simulación mezclados con datos reales.')
    indices = principal.get('_index', pd.Series('',index=principal.index))
    if indices.ne('').any() and (indices.eq('').any() or indices.duplicated().any()):
        raise ErrorDatos('_index vacío o duplicado: no es posible vincular las hojas repetidas.')
    padres = dict(zip(indices,principal.id_hogar))
    hogares=[]; estados=[]; certs=[]; ventas=[]; avisos=[]
    for _,r in principal.iterrows():
        h={c:texto(r.get(c,'')) for c in CODIGOS}
        # El servidor identifica la cuenta que envió; no se usa para identificar al productor.
        h['encuestador']=texto(r.get('_submitted_by','')) or h['encuestador']
        for c in CODIGOS:
            raw=texto(r.get(c+'_respuesta',h[c])); estado=texto(r.get(c+'_estado',''))
            if raw in ('NS','NR','NA'):
                h[c]=''; estado=raw
            if estado in ('NS','NR','NA'): h[c]=''
            if estado: estados.append(dict(id_hogar=h['id_hogar'],campo=c,estado=estado,fuente='KOBO',nota=''))
        if h['pago_inclusion']=='':
            # Mantener incertidumbre como faltante, sin imputar prima adicional.
            # La sensibilidad del motor también reconoce NR, NS y vacío.
            pass
        hogares.append(h)
        if texto(r.get('pm_cat_decl_respuesta',''))=='FUERA':
            h['pm_cat_decl']='FUERA'
            avisos.append(dict(id_hogar=h['id_hogar'],campo='pm_cat_decl',mensaje='FUERA: se conserva en el archivo original; no se convierte a porcentaje.'))
    def vincular(t,r):
        p=texto(r.get('_parent_index',''))
        if not p or p not in padres: raise ErrorDatos('Repetición sin _parent_index válido en la hoja principal.')
        return padres[p]
    for n,t in hojas.items():
        if 'esquema_nombre' in t:
            for _,r in t.iterrows():
                id=vincular(t,r); h=next(x for x in hogares if x['id_hogar']==id)
                anual=texto(r.get('cert_anual',r.get('cert_anual_respuesta','')))
                todo=texto(r.get('cert_todo',r.get('cert_todo_respuesta','')))
                inicio=fecha(r.get('cert_inicio_fecha','')); fin=fecha(r.get('cert_fin_fecha',''))
                anio=texto(r.get('cert_inicio_anio',''))
                if anual=='1' and anio and float(anio)>2025:
                    raise ErrorDatos(f'{id}: inicio de certificación posterior al inicio del periodo, pero declara cobertura anual.')
                if h['grupo_cert']=='C1' and (anual!='1' or todo!='1'):
                    raise ErrorDatos(f'{id}: C1 requiere confirmar cobertura anual y total en cada certificación. Revise su clasificación.')
                nombre=texto(r.get('esquema_nombre',''))
                if not nombre: raise ErrorDatos(f'{id}: certificación sin nombre.')
                certs.append(dict(id_hogar=id,esquema_id=nombre,norma_alcance=texto(r.get('norma_alcance','')),
                    inicio=inicio,fin=fin,area_ha=h['area_saf_ha'] if todo=='1' else texto(r.get('cert_area_ha','')),
                    cubre_periodo_completo=anual if anual in ('0','1') else '',fuente=texto(r.get('cert_fuente',r.get('cert_fuente_respuesta','')))))
                if not inicio:
                    avisos.append(dict(id_hogar=id,campo='cert_inicio_fecha',mensaje='Sin fecha exacta: cobertura anual basada en declaración, no verificación documental. No se inventó una fecha.'))
        if 'venta_importe' in t:
            for j,(_,r) in enumerate(t.iterrows()):
                id=vincular(t,r)
                ventas.append(dict(id_hogar=id,operacion_id=str(j+1),presentacion=texto(r.get('venta_presentacion','')),
                    cantidad_original=texto(r.get('venta_cantidad','')),unidad_original=texto(r.get('venta_unidad','')),
                    kg_por_unidad='1' if texto(r.get('venta_unidad',''))=='KG' else texto(r.get('venta_kg_unidad','')),
                    importe_usd=texto(r.get('venta_importe','')),fuente='KOBO'))
    for _,r in principal.iterrows():
        id=r.id_hogar
        for contador,lista in [('n_certificados',certs),('n_ventas',ventas)]:
            n=texto(r.get(contador,''))
            if n and float(n)!=sum(x['id_hogar']==id for x in lista):
                raise ErrorDatos(f'{id}: {contador} no coincide con las filas repetidas. Incluya todas las hojas del Excel.')
    meta=[dict(clave=k,valor=v) for k,v in dict(tipo_datos='SIMULACION' if etapa=='SIMULACION' else 'CAMPO',
        etapa=etapa,periodo_inicio=PERIODO[0],periodo_fin=PERIODO[1],diseno='NO_DEFINIDO',version_app=VERSION).items()]
    return dict(Hogares=hogares,Estados=estados,Certificaciones=certs,Ventas=ventas,Metadatos=meta),avisos

def ejecutar_archivo(contenido, nombre, diseno='NO_DEFINIDO', demo=False):
    """Devuelve tablas resumidas y un ZIP reproducible; no transmite datos."""
    import analisis_doctoral, analisis_pregrado
    raiz=Path('/trabajo') if Path('/home/pyodide').exists() else Path(__file__).parent.parent/'tests'/'_salida'
    if raiz.exists(): shutil.rmtree(raiz)
    entrada=raiz/'entrada'; entrada.mkdir(parents=True)
    avisos=[]
    if nombre.lower().endswith('.json'):
        if not demo: raise ErrorDatos('JSON solo se utiliza para la demostración interna. Para sus datos cargue XLSX de Kobo.')
        datos=json.loads(contenido)
        if not all(str(x.get('id_hogar','')).startswith('SIM') for x in datos['Hogares']):
            raise ErrorDatos('La demostración contiene identificadores no ficticios.')
    else:
        hojas=pd.read_excel(io.BytesIO(contenido),sheet_name=None,dtype=str,keep_default_na=False,engine='openpyxl')
        datos,avisos=adaptar_kobo(hojas)
    md={x['clave']:x['valor'] for x in datos['Metadatos']}
    etapa=md.get('etapa',md.get('tipo_datos'))
    if demo: diseno='aleatorio_simple_independiente'
    if etapa=='PILOTO': diseno='NO_DEFINIDO'
    md.update(diseno=diseno,version_app=VERSION,sha256_entrada=hashlib.sha256(contenido).hexdigest(),archivo=nombre)
    datos['Metadatos']=[dict(clave=k,valor=v) for k,v in md.items()]
    for n,cols in [('Hogares',CODIGOS),('Certificaciones',CERT_COLS),('Ventas',VENTAS_COLS),('Estados',ESTADOS_COLS),('Metadatos',['clave','valor'])]:
        pd.DataFrame(datos[n],columns=cols).to_csv(entrada/(n+'.csv'),index=False,encoding='utf-8-sig')
    # Trazabilidad de columnas originales (incluye estados de repeticiones); nunca se publica en GitHub.
    if not demo:
        for j,(n,t) in enumerate(hojas.items()):
            t.to_csv(raiz/f'original_hoja_{j+1}.csv',index=False,encoding='utf-8-sig')
        (raiz/'hojas_originales.json').write_text(json.dumps(list(hojas),ensure_ascii=False),encoding='utf-8')
    (raiz/'entrada_sha256.txt').write_text(md['sha256_entrada'],encoding='utf-8')
    pd.DataFrame(avisos,columns=['id_hogar','campo','mensaje']).to_csv(raiz/'avisos_importacion.csv',index=False,encoding='utf-8-sig')
    analisis_doctoral.ejecutar(entrada,raiz/'doctoral')
    analisis_pregrado.ejecutar(entrada,raiz/'pregrado')
    def leer(p):
        try: return pd.read_csv(raiz/p).fillna('').to_dict(orient='records')
        except pd.errors.EmptyDataError: return []
    grupos=pd.Series([x['grupo_cert'] for x in datos['Hogares'] if str(x['consiente'])=='1' and str(x['saf_confirmado'])=='1']).value_counts().to_dict()
    result=dict(etapa=etapa,diseno=diseno,grupos=grupos,version=VERSION,
        economicos=leer('doctoral/contrastes_economicos.csv'),sociales=leer('doctoral/contrastes_sociales.csv'),
        modelo=leer('doctoral/modelo_HC3.csv'),modelo_info=leer('doctoral/informacion_modelo.csv'),
        sostenibilidad=leer('pregrado/resumen_indices.csv'),relativizacion=leer('pregrado/parametros_relativizacion.csv'),
        cobertura=leer('pregrado/cobertura_indicadores.csv'),
        avisos=avisos+leer('doctoral/avisos_validacion.csv'),
        n_analizados=len(leer('doctoral/indicadores_hogares.csv')),
        informes={n:(raiz/n/'reporte.html').read_text(encoding='utf-8') for n in ('doctoral','pregrado')})
    from redaccion import generar_documentos
    ejecucion=json.loads((raiz/'doctoral'/'ejecucion.json').read_text(encoding='utf-8'))
    result['documentos']=generar_documentos(result,md,ejecucion,leer('pregrado/comparaciones_indices.csv'))
    for tesis, apartados in result['documentos'].items():
        for apartado, contenido_md in apartados.items():
            (raiz/tesis/(apartado+'.md')).write_bytes(contenido_md.encode('utf-8'))
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(raiz.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(raiz))
        for p in Path(__file__).parent.glob('*.py'): z.write(p,'codigo/'+p.name)
        z.write(Path(__file__).parent/'configuracion.json','codigo/configuracion.json')
    return json.dumps(result,ensure_ascii=False,allow_nan=False),buffer.getvalue()
