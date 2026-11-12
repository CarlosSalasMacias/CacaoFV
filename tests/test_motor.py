"""Pruebas reproducibles: python -m unittest discover -s tests -v (desde CacaoFV)."""
import sys, json, copy, unittest, io, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
import pandas as pd
import numpy as np
from unittest.mock import patch
from aplicacion import adaptar_kobo, columnas, ejecutar_archivo, PERIODO
from comun import ErrorDatos, derivar
from analisis_pregrado import normalizar

ROOT=Path(__file__).resolve().parents[1]

def fixture():
    origen=json.loads((ROOT/'demo'/'base_ficticia.json').read_text(encoding='utf-8'))
    ids={r['id_hogar']:'SIM_'+r['id_hogar'] for r in origen['Hogares']}
    principal=[];cert=[]
    for i,r in enumerate(origen['Hogares'],1):
        x=r.copy();x.update(id_hogar=ids[r['id_hogar']],_index=str(i),tipo_levantamiento='SIMULACION',periodo_inicio=PERIODO[0],periodo_fin=PERIODO[1])
        cs=[c for c in origen['Certificaciones'] if c['id_hogar']==r['id_hogar']]
        x['n_certificados']=str(len(cs));x['n_ventas']='0';x['salud_acceso_estado']='VALIDO'
        for e in origen['Estados']:
            if e['id_hogar']==r['id_hogar']: x[e['campo']+'_estado']=e['estado']
        principal.append(x)
        for c in cs:
            cert.append(dict(_parent_index=str(i),esquema_nombre=c['esquema_id'],norma_alcance=c['norma_alcance'],cert_anual=c['cubre_periodo_completo'],cert_todo='1' if float(c['area_ha'])>=float(r['area_saf_ha'])-1e-6 else '0',cert_area_ha=c['area_ha'],cert_inicio_fecha=c['inicio'],cert_fin_fecha=c['fin'],cert_fuente=c['fuente']))
    # Los estados de datos opcionales se representan exactamente según el origen.
    for r in principal:
        if not str(r.get('salud_acceso','')).strip(): r['salud_acceso_estado']=next((e['estado'] for e in origen['Estados'] if ids[e['id_hogar']]==r['id_hogar'] and e['campo']=='salud_acceso'),'NS')
    return {'encuesta':pd.DataFrame(principal).fillna('').map(str),'certificaciones':pd.DataFrame(cert).fillna('').map(str)}

class Motor(unittest.TestCase):
    def test_rutas(self):
        self.assertEqual(list(columnas(pd.DataFrame({'q1/id_hogar':['A']}))),['id_hogar'])
        with self.assertRaises(ErrorDatos): columnas(pd.DataFrame({'q1/id_hogar':['A'],'q2/id_hogar':['B']}))
    def test_repeticiones_no_multiplican_hogares(self):
        d,_=adaptar_kobo(fixture());self.assertEqual(len(d['Hogares']),120);self.assertGreater(len(d['Certificaciones']),120)
    def test_margen_certificacion_sin_fecha_inventada(self):
        t=fixture();t['certificaciones']['cert_inicio_fecha']='';d,a=adaptar_kobo(t)
        self.assertTrue(all(x['inicio']=='' for x in d['Certificaciones']));self.assertTrue(a)
    def test_estados_y_cero(self):
        t=fixture();t['encuesta'].loc[0,'vc_usd']='0';t['encuesta'].loc[0,'vc_usd_estado']='VALIDO'
        t['encuesta'].loc[1,'salud_acceso']='';t['encuesta'].loc[1,'salud_acceso_respuesta']='NA'
        d,_=adaptar_kobo(t);self.assertEqual(d['Hogares'][0]['vc_usd'],'0');self.assertEqual(d['Hogares'][1]['salud_acceso'],'')
        self.assertTrue(any(e['id_hogar']==d['Hogares'][1]['id_hogar'] and e['campo']=='salud_acceso' and e['estado']=='NA' for e in d['Estados']))
    def test_huerfana(self):
        t=fixture();t['certificaciones'].loc[0,'_parent_index']='9999'
        with self.assertRaises(ErrorDatos): adaptar_kobo(t)
    def test_periodos_etapas_conteos(self):
        for campo,valor in [('periodo_inicio','2026-01-01'),('tipo_levantamiento','CAMPO'),('n_certificados','99')]:
            with self.subTest(campo=campo):
                t=fixture();t['encuesta'].loc[1,campo]=valor
                with self.assertRaises(ErrorDatos): adaptar_kobo(t)
    def test_c1_contradictorio(self):
        t=fixture();t['certificaciones'].loc[0,'cert_anual']='0'
        with self.assertRaises(ErrorDatos): adaptar_kobo(t)
    def test_relativizacion_constante_y_sentido(self):
        z,p=normalizar(pd.DataFrame({'A':[2,2,2],'B':[0,5,10]}),{'A':('ecologica',1),'B':('social',-1)})
        self.assertTrue(z.A.isna().all());self.assertEqual(z.B.tolist(),[1,.5,0]);self.assertFalse(bool(p.iloc[0].activo))
    def test_demo_completa_y_sensibilidad(self):
        r,z=ejecutar_archivo((ROOT/'demo/base_ficticia.json').read_bytes(),'demo.json',demo=True);r=json.loads(r)
        self.assertEqual(r['n_analizados'],120)
        bf=next(x for x in r['economicos'] if x['variable']=='bf_usd')
        self.assertEqual((bf['n_C0'],bf['n_C1']),(39,71));self.assertAlmostEqual(bf['diferencia_C1_C0'],1702.884112,places=5)
        with zipfile.ZipFile(io.BytesIO(z)) as f:
            self.assertIn('doctoral/reporte.html',f.namelist());self.assertIn('pregrado/indices_hogares.csv',f.namelist())
            for tesis in ('doctoral','pregrado'):
                for apartado in ('metodologia','resultados_discusion'):
                    borrador=r['documentos'][tesis][apartado]
                    self.assertEqual(f.read(f'{tesis}/{apartado}.md').decode('utf-8'),borrador)
                    self.assertIn('Simulación con hogares ficticios',borrador)
            self.assertIn('1702,88 USD/hogar/año',r['documentos']['doctoral']['resultados_discusion'])
            self.assertIn('115 de los 120 hogares',r['documentos']['pregrado']['resultados_discusion'])
            self.assertIn('Pachay Delgado, L. E. (2024)',r['documentos']['pregrado']['metodologia'])
            d=pd.read_csv(f.open('doctoral/indicadores_hogares.csv'))
            self.assertTrue((d.bf_usd.dropna()<0).any());self.assertTrue((d.j_fam_8h==0).any())
            self.assertEqual(int(pd.read_csv(f.open('pregrado/indices_hogares.csv')).IS.notna().sum()),115)
    def test_kobo_piloto_inhabilita_inferencia(self):
        t=fixture();t['encuesta']['tipo_levantamiento']='PILOTO'
        t['encuesta']['id_hogar']=['FV-'+str(i+1).zfill(3) for i in range(120)]
        with patch('aplicacion.pd.read_excel',return_value=t):
            r,z=ejecutar_archivo(b'fixture de lectura, no archivo real','prueba.xlsx','aleatorio_simple_independiente')
        r=json.loads(r);self.assertEqual(r['etapa'],'PILOTO');self.assertEqual(r['diseno'],'NO_DEFINIDO')
        self.assertTrue(all(x['p']=='' for x in r['economicos']))
        self.assertEqual(r['n_analizados'],120)
        for tesis,docs in r['documentos'].items():
            self.assertIn('El piloto se procesó en modalidad descriptiva',docs['metodologia'])
            self.assertIn('## Referencias',docs['metodologia'])
            self.assertIn('La comparación de este indicador es descriptiva',docs['resultados_discusion'])
            self.assertNotIn('valor p de Welch',docs['resultados_discusion'])

if __name__=='__main__': unittest.main()
