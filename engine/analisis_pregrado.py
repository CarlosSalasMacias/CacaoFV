"""Relativización conjunta y comparación del índice. Uso: python analisis_pregrado.py entrada.xlsx --salida carpeta"""
from pathlib import Path
import sys, argparse, math
sys.path.insert(0,str(Path(__file__).resolve().parent/"_deps_prueba"))
import numpy as np
import pandas as pd
from comun import cargar, guardar, reporte, config, ErrorDatos
from analisis_doctoral import welch, holm

ESPEC={
    "E1":("economica",1),"E2":("economica",1),"E3":("economica",1),"E4":("economica",1),"E5":("economica",1),
    "A1":("ecologica",1),"A2":("ecologica",-1),"A3":("ecologica",-1),"A4":("ecologica",1),
    "S1":("social",-1),"S2":("social",1),"S3":("social",1),"S4":("social",-1),"S5":("social",1),"S6":("social",1),
}

def crudos(d):
    x=pd.DataFrame(index=d.index)
    x["E1"]=d.cfp_usd/(d.gi_usd+d.p_usd).where(d.gi_usd+d.p_usd>0)
    x["E2"]=d.bf_persona_usd
    fuentes=d[["vc_usd","vo_usd","ac_usd","o_negocio_usd","o_trab_usd","o_transf_usd"]]
    x["E3"]=(fuentes>0).sum(axis=1).where(fuentes.notna().all(axis=1))
    x["E4"]=d.registro_econ; x["E5"]=d.apoyo_aplicado
    x["A1"]=d[[f"pract_{i}" for i in range(1,5)]].sum(axis=1,min_count=4)
    x["A2"]=d.n_aplic_plag; x["A3"]=d.conv_bosque; x["A4"]=d.arboles_especies_cat
    x["S1"]=d.alim_reduc_cat; x["S2"]=d.salud_acceso; x["S3"]=d.escuela_asist
    x["S4"]=d.transp_dific; x["S5"]=d.decision_part; x["S6"]=d.satisf_saf
    return x

def normalizar(x,espec):
    z=pd.DataFrame(index=x.index); parametros=[]
    for c,(dim,signo) in espec.items():
        m=x[c].min(); M=x[c].max(); activo=bool(pd.notna(m) and pd.notna(M) and M>m)
        parametros.append(dict(indicador=c,dimension=dim,direccion=signo,minimo=m,maximo=M,n_valido=int(x[c].notna().sum()),activo=activo,
                               motivo="" if activo else "Sin datos o constante: excluido globalmente"))
        z[c]=(x[c]-m)/(M-m) if activo and signo==1 else ((M-x[c])/(M-m) if activo else np.nan)
    return z,pd.DataFrame(parametros)

def dimensiones(z,param,na,cfg):
    resultado=pd.DataFrame(index=z.index)
    for dim in ("economica","ecologica","social"):
        cols=param.loc[(param.dimension==dim)&param.activo,"indicador"].tolist()
        if not cols:
            resultado[dim]=np.nan;resultado[dim+"_validos"]=0;resultado[dim+"_aplicables"]=0;continue
        aplicables=(~na[cols]).sum(axis=1)
        validos=z[cols].notna().sum(axis=1)
        umbral=np.ceil(aplicables*cfg["min_cobertura"])
        cumple=(aplicables>0)&(validos>=umbral)
        if dim=="social": cumple &= validos>=cfg["social_min_validos"]
        resultado[dim]=z[cols].mean(axis=1).where(cumple)
        resultado[dim+"_validos"]=validos;resultado[dim+"_aplicables"]=aplicables
    pesos=cfg["pesos_dimensiones"]
    if not np.isclose(sum(pesos.values()),1): raise ErrorDatos("Pesos de dimensiones deben sumar uno")
    resultado["IS"]=sum(resultado[c]*pesos[c] for c in ("economica","ecologica","social"))
    comunes=[c for c in ["S1","S4","S6"] if c in z and param.set_index("indicador").loc[c,"activo"]]
    resultado["social_comun"]=z[comunes].mean(axis=1).where(z[comunes].notna().all(axis=1)) if comunes else np.nan
    resultado["IS_comun"]=resultado.economica*pesos["economica"]+resultado.ecologica*pesos["ecologica"]+resultado.social_comun*pesos["social"]
    return resultado

def ejecutar(entrada,salida):
    out=Path(salida);cfg=config(); d,estados,md=cargar(entrada,out); x=crudos(d); espec=ESPEC.copy()
    if cfg["pregrado"]["incluir_agua"]:
        ap=d[[f"agua_aplica_{i}" for i in range(1,4)]]
        total=ap.sum(axis=1,min_count=3)
        valores=[]
        for i,row in d.iterrows():
            pert=[j for j in (1,2,3) if row[f"agua_aplica_{j}"]==1]
            vals=[row[f"agua_{j}"] for j in pert]
            valores.append(np.mean(vals) if vals and all(pd.notna(v) for v in vals) and ap.loc[i].notna().all() else np.nan)
        x["A5"]=valores;espec["A5"]=("ecologica",1)
    z,param=normalizar(x,espec)
    # Solo NA estructural reduce el denominador. NS/NR/vacío no lo reducen.
    na=pd.DataFrame(False,index=d.index,columns=x.columns)
    mapa={"salud_acceso":"S2","escuela_asist":"S3","decision_part":"S5"}
    for r in estados.itertuples():
        if r.estado=="NA" and r.campo in mapa:
            na.loc[d.index[d.id_hogar==r.id_hogar],mapa[r.campo]]=True
    if "A5" in x:
        na["A5"]=d[[f"agua_aplica_{i}" for i in (1,2,3)]].eq(0).all(axis=1)
    indices=dimensiones(z,param,na,cfg["pregrado"])
    indices.insert(0,"grupo_cert",d.grupo_cert);indices.insert(0,"id_hogar",d.id_hogar)
    indices["clase_relativa"]=pd.cut(indices.IS,bins=[-1e-10,.2,.4,.6,.8,1.0000001],labels=["<0.2","0.2 a <0.4","0.4 a <0.6","0.6 a <0.8","0.8 a 1"],right=False)
    resumen=[]
    for g,s in indices.groupby("grupo_cert"):
        for c in ["economica","ecologica","social","IS","social_comun","IS_comun"]:
            a=s[c].dropna();resumen.append(dict(grupo=g,indice=c,n=len(a),no_calculable=len(s)-len(a),media=a.mean(),de=a.std(),mediana=a.median(),p25=a.quantile(.25),p75=a.quantile(.75)))
    permitido=md.get("diseno")=="aleatorio_simple_independiente"
    comparaciones=holm(pd.DataFrame([welch(indices,c,permitido) for c in ["economica","ecologica","social","IS","social_comun","IS_comun"]]))
    detalle=x.add_prefix("crudo_").join(z.add_prefix("I_")); detalle.insert(0,"id_hogar",d.id_hogar)
    cobertura=[]
    for g,s in d.groupby("grupo_cert"):
        for c in x:
            vals=x.loc[s.index,c];cobertura.append(dict(grupo=g,indicador=c,n_total=len(s),n_valido=int(vals.notna().sum()),n_NA=int(na.loc[s.index,c].sum()),n_otros_faltantes=int((vals.isna()&~na.loc[s.index,c]).sum())))
    for name,t in {"indicadores_crudos_normalizados":detalle,"parametros_relativizacion":param,"indices_hogares":indices,
                   "resumen_indices":pd.DataFrame(resumen),"comparaciones_indices":comparaciones,"cobertura_indicadores":pd.DataFrame(cobertura)}.items(): guardar(t,out/(name+".csv"))
    reporte(out,"Sostenibilidad por relativización conjunta",md,[("Resumen de dimensiones e índices",pd.DataFrame(resumen)),("Comparación C1 frente a C0",comparaciones),("Referencias comunes de relativización",param)],
            ["Mínimos y máximos se calculan sobre todos los hogares elegibles del archivo, incluidos C2/C3, una sola vez; nunca por grupo de certificación.",
             "Índices relativos a esta muestra. Uno no acredita sostenibilidad absoluta; una etiqueta baja no demuestra colapso.",
             "Los indicadores constantes se excluyen para todos los hogares. Si desaparece una dimensión, no se calcula IS.",
             "Cobertura mínima por dimensión 80% de indicadores aplicables; social exige además cuatro válidos. NS y NR no son NA.",
             "IS_comun usa la dimensión social común S1 S4 S6 como sensibilidad; no reemplaza silenciosamente el IS principal.",
             "La certificación no otorga puntos. Los mismos indicadores y referencias se aplican a C0 y C1.",
             "No comparar índices de archivos diferentes sin fijar la misma referencia de normalización. Revisar los parámetros exportados."])
    print(f"Pregrado terminado: {out.resolve()}")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("entrada");p.add_argument("--salida",default="resultados_pregrado");a=p.parse_args()
    try: ejecutar(a.entrada,a.salida)
    except ErrorDatos as e:p.exit(2,"Datos no analizables: "+str(e)+"\n")
