"""Carga, validación y cálculos compartidos. Solo lee Excel; no lo reescribe."""
from pathlib import Path
import json, sys, platform, html
import numpy as np
import pandas as pd
from esquema import CAMPOS, CODIGOS, INDICE, CERT_COLS, VENTAS_COLS, ESTADOS_COLS, ROOT, CONFIG

class ErrorDatos(ValueError):
    pass

def config():
    p = ROOT/"configuracion.json"
    cfg=json.loads(p.read_text(encoding="utf-8")) if p.exists() else CONFIG.copy()
    if cfg.get("alpha")!=0.05: raise ErrorDatos("Esta versión usa IC95% y alfa 0,05. Cambiar alfa requiere adaptar las fórmulas del análisis.")
    return cfg

def tabla(path, nombre, columnas):
    path=Path(path)
    if path.is_dir():
        archivo=path/(nombre+".csv")
        if not archivo.exists(): raise ErrorDatos(f"Falta {archivo}")
        t=pd.read_csv(archivo, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    else:
        t=pd.read_excel(path,sheet_name=nombre,dtype=str,keep_default_na=False,engine="openpyxl")
    faltan=set(columnas)-set(t.columns)
    if faltan: raise ErrorDatos(f"{nombre}: faltan columnas {sorted(faltan)}")
    t=t[columnas].fillna("").apply(lambda c:c.astype(str).str.strip())
    return t.loc[(t!="").any(axis=1)].copy()

def cargar(path, out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    d=tabla(path,"Hogares",CODIGOS)
    if d.empty: raise ErrorDatos("La base está vacía. Primero capture o consolide hogares.")
    cert=tabla(path,"Certificaciones",CERT_COLS)
    ventas=tabla(path,"Ventas",VENTAS_COLS)
    estados=tabla(path,"Estados",ESTADOS_COLS)
    meta=tabla(path,"Metadatos",["clave","valor"])
    if meta.clave.eq("").any() or meta.clave.duplicated().any(): raise ErrorDatos("Metadatos: clave vacía o duplicada")
    md=dict(zip(meta.clave,meta.valor))
    if md.get("tipo_datos") not in ("SIMULACION","CAMPO"):
        raise ErrorDatos("Metadatos.tipo_datos debe indicar SIMULACION o CAMPO")
    if not md.get("periodo_inicio") or not md.get("periodo_fin"):
        raise ErrorDatos("Falta periodo común en Metadatos")
    ini=pd.Timestamp(md["periodo_inicio"]); fin=pd.Timestamp(md["periodo_fin"])
    if not 350 <= (fin-ini).days+1 <= 370: raise ErrorDatos("El periodo debe abarcar aproximadamente 12 meses completos")
    if d.id_hogar.eq("").any() or d.id_hogar.duplicated().any(): raise ErrorDatos("ID vacío o duplicado en Hogares")
    for nombre,t in [("Certificaciones",cert),("Ventas",ventas),("Estados",estados)]:
        if (~t.id_hogar.isin(d.id_hogar)).any(): raise ErrorDatos(f"{nombre}: ID no presente en Hogares")
    if estados.duplicated(["id_hogar","campo"]).any(): raise ErrorDatos("Estados: duplicado hogar/campo")
    if (~estados.campo.isin(CODIGOS)).any(): raise ErrorDatos("Estados: nombre de campo desconocido")
    if (~estados.estado.isin(["NS","NR","NA","VALIDO"])).any(): raise ErrorDatos("Estado no válido: use NS NR NA VALIDO")
    warnings=[]
    def aviso(id,c,m): warnings.append(dict(id_hogar=id,campo=c,mensaje=m))
    if (~d.consiente.isin(["0","1",""])).any() or (~d.saf_confirmado.isin(["0","1",""])).any():
        raise ErrorDatos("Consentimiento y SAF confirmado deben ser 0, 1 o vacío")
    elegible=d.consiente.eq("1")&d.saf_confirmado.eq("1")
    md["n_registros_entrada"]=str(len(d));md["n_excluidos_no_elegibles"]=str(int((~elegible).sum()))
    for id in d.loc[~elegible,"id_hogar"]: aviso(id,"elegibilidad","No se analiza: falta consentimiento o SAF confirmado")
    d=d.loc[elegible].copy()
    if d.empty: raise ErrorDatos("No hay hogares con consentimiento y SAF confirmado")
    cert=cert[cert.id_hogar.isin(d.id_hogar)].copy();ventas=ventas[ventas.id_hogar.isin(d.id_hogar)].copy();estados=estados[estados.id_hogar.isin(d.id_hogar)].copy()
    sm={(r.id_hogar,r.campo):r.estado for r in estados.itertuples()}
    for f in CAMPOS:
        c=f["codigo"]; s=d[c]
        if f["tipo"] in ("numero","entero"):
            x=pd.to_numeric(s.replace("",np.nan),errors="coerce")
            if ((s!="")&x.isna()).any(): raise ErrorDatos(f"{c}: texto en campo numérico; no escriba NS/NA ni unidades aquí")
            if x.notna().any() and not np.isfinite(x.dropna()).all(): raise ErrorDatos(f"{c}: valor no finito")
            if f["tipo"]=="entero" and ((x.dropna()%1).abs()>1e-8).any(): raise ErrorDatos(f"{c}: requiere enteros")
            if f["minimo"] is not None and (x<f["minimo"]).any(): raise ErrorDatos(f"{c}: valor bajo mínimo {f['minimo']}")
            if f["maximo"] is not None and (x>f["maximo"]).any(): raise ErrorDatos(f"{c}: valor sobre máximo")
            d[c]=x
        if f["opciones"]:
            no_blank=d[c].notna() & d[c].astype(str).ne("")
            if (~d.loc[no_blank,c].isin(f["opciones"])).any(): raise ErrorDatos(f"{c}: categoría fuera del diccionario")
        for i in d.index:
            id=d.at[i,"id_hogar"]; val=d.at[i,c]; missing=pd.isna(val) or val==""
            estado=sm.get((id,c))
            if estado in ("NS","NR","NA") and not missing: raise ErrorDatos(f"{id}/{c}: tiene valor y estado faltante a la vez")
            if estado=="VALIDO" and missing: raise ErrorDatos(f"{id}/{c}: VALIDO sin respuesta")
            if missing and not estado and f["tipo"] in ("numero","entero"):
                aviso(id,c,"Vacío sin motivo. Se trata como faltante aplicable, nunca como cero.")
    if (d.n_trab_fam>d.n_hogar).any(): raise ErrorDatos("Trabajadores familiares mayores que miembros del hogar")
    if (d.area_saf_ha>d.area_total_ha).any(): raise ErrorDatos("Área SAF mayor que área total")
    for r in d.itertuples():
        if r.grupo_cert=="": raise ErrorDatos(f"{r.id_hogar}: falta clasificación de certificación")
        if r.plag_sint==0 and r.n_aplic_plag>0: raise ErrorDatos(f"{r.id_hogar}: no usa plaguicidas pero declara aplicaciones")
        if r.plag_sint==1 and r.n_aplic_plag==0: raise ErrorDatos(f"{r.id_hogar}: usa plaguicidas con cero aplicaciones")
        if r.conv_bosque==0 and r.conv_bosque_ha>0: raise ErrorDatos(f"{r.id_hogar}: conversión contradictoria")
        if r.pago_inclusion=="PARCIAL" and (pd.isna(r.pago_incluido_usd) or r.pago_incluido_usd>r.pago_cert_decl_usd):
            raise ErrorDatos(f"{r.id_hogar}: conciliación parcial del pago incorrecta")
        if r.grupo_cert=="C0" and r.pago_cert_decl_usd>0: raise ErrorDatos(f"{r.id_hogar}: pago por certificación en C0; revisar periodo")
        for pref in ("benef_","dific_"):
            vals=[getattr(r,c) for c in CODIGOS if c.startswith(pref)]
            if sum(v for v in vals if not pd.isna(v))>2: raise ErrorDatos(f"{r.id_hogar}: más de dos opciones priorizadas {pref}")
            ninguno=getattr(r,"benef_ninguno" if pref=="benef_" else "dific_ninguna")
            if ninguno==1 and sum(v for v in vals if not pd.isna(v))>1: raise ErrorDatos(f"{r.id_hogar}: ninguna opción no puede combinarse con otra {pref}")
        for i in (1,2,3):
            if getattr(r,f"agua_aplica_{i}")==0 and not pd.isna(getattr(r,f"agua_{i}")):
                raise ErrorDatos(f"{r.id_hogar}: práctica de agua no aplicable debe quedar vacía con estado NA")
    if cert.duplicated(["id_hogar","esquema_id"]).any(): raise ErrorDatos("Certificación duplicada; en esta versión una fila resume un esquema por hogar")
    for r in cert.itertuples():
        area=pd.to_numeric(r.area_ha,errors="coerce")
        if r.area_ha and (pd.isna(area) or area<=0): raise ErrorDatos(f"{r.id_hogar}: área de certificación inválida")
        hogar=d.set_index("id_hogar").loc[r.id_hogar]
        if area>hogar.area_saf_ha+1e-6: raise ErrorDatos(f"{r.id_hogar}: área certificada superior al SAF")
        if r.cubre_periodo_completo not in ("0","1",""): raise ErrorDatos("Certificaciones: cobertura completa debe ser 0 o 1, o vacío si no se conoce")
        for fecha in (r.inicio,r.fin):
            if fecha and pd.isna(pd.to_datetime(fecha,errors="coerce")): raise ErrorDatos("Fecha de certificación inválida")
        if r.inicio and r.fin and pd.Timestamp(r.inicio)>pd.Timestamp(r.fin): raise ErrorDatos("Inicio de certificado posterior a fin")
        if r.cubre_periodo_completo=="1" and ((r.inicio and pd.Timestamp(r.inicio)>ini) or (r.fin and pd.Timestamp(r.fin)<fin)):
            raise ErrorDatos(f"{r.id_hogar}: las fechas contradicen cobertura anual")
        if hogar.grupo_cert=="C0": raise ErrorDatos(f"{r.id_hogar}: C0 con una certificación listada; no incluir registros históricos en esta tabla")
    for r in d.itertuples():
        cs=cert[cert.id_hogar==r.id_hogar]
        if r.grupo_cert=="C1" and cs.empty: raise ErrorDatos(f"{r.id_hogar}: C1 sin detalle de certificación")
        if r.grupo_cert=="C1" and not any((cs.cubre_periodo_completo=="1") & (pd.to_numeric(cs.area_ha,errors="coerce")>=r.area_saf_ha-1e-6)):
            raise ErrorDatos(f"{r.id_hogar}: C1 sin cobertura completa demostrable; revisar lotes/cobertura")
    if ventas.duplicated(["id_hogar","operacion_id"]).any(): raise ErrorDatos("Ventas: operación duplicada por hogar")
    for c in ["cantidad_original","kg_por_unidad","importe_usd"]:
        original=ventas[c].copy(); ventas[c]=pd.to_numeric(ventas[c].replace("",np.nan),errors="coerce")
        if ((original!="")&ventas[c].isna()).any() or (ventas[c]<0).any(): raise ErrorDatos(f"Ventas/{c}: valor inválido")
    for id,vs in ventas.groupby("id_hogar"):
        total=vs.importe_usd.sum(min_count=len(vs)); declarado=d.set_index("id_hogar").loc[id,"vc_usd"]
        if pd.notna(total) and pd.notna(declarado) and abs(total-declarado)>0.05:
            raise ErrorDatos(f"{id}: ventas detalladas no concuerdan con vc_usd. Ventas debe contener todo el año o dejarse sin filas.")
    d["combo_cert"]=d.id_hogar.map(cert.groupby("id_hogar").esquema_id.apply(lambda x:"+".join(sorted(set(x))))).fillna("SIN")
    d["n_esquemas"]=d.id_hogar.map(cert.groupby("id_hogar").esquema_id.nunique()).fillna(0)
    d["cert_estable"]=d.grupo_cert.map({"C0":0,"C1":1})
    d=derivar(d)
    for i,r in d.iterrows():
        if pd.notna(r.cf_usd) and pd.notna(r.cubre_gastos_decl) and int(r.cf_usd>=0)!=r.cubre_gastos_decl:
            aviso(r.id_hogar,"cubre_gastos_decl","No coincide con flujo de ventas. Revisar sin corregir automáticamente.")
    for key in ("consiente","saf_confirmado"):
        if (d[key]!=1).any(): warnings.append(dict(id_hogar="",campo=key,mensaje="Se excluyen hogares sin confirmación/consentimiento"))
    d=d[(d.consiente==1)&(d.saf_confirmado==1)].copy()
    pd.DataFrame(warnings,columns=["id_hogar","campo","mensaje"]).to_csv(out/"avisos_validacion.csv",index=False,encoding="utf-8-sig")
    return d, estados, md

def derivar(d):
    d=d.copy()
    def suma(cols): return d[cols].sum(axis=1,min_count=len(cols))
    d["vo_usd"]=suma(["vo_alim_usd","vo_otro_usd"])
    d["gi_usd"]=suma(["vc_usd","vo_usd"])
    d["ac_usd"]=suma(["ac_alim_usd","ac_otro_usd"])
    d["cc_usd"]=suma(["cc_ins_usd","cc_moc_usd","cc_trans_usd","cc_cert_usd","cc_otros_usd"])
    p=pd.Series(np.nan,index=d.index)
    p.loc[d.pago_inclusion=="SI"]=0
    p.loc[d.pago_inclusion=="NO"]=d.pago_cert_decl_usd
    parcial=d.pago_inclusion=="PARCIAL"
    p.loc[parcial]=d.pago_cert_decl_usd-d.pago_incluido_usd
    p.loc[(d.grupo_cert=="C0") | (d.pago_cert_decl_usd==0)]=0
    d["p_usd"]=p
    d["cf_usd"]=d.gi_usd-d.cc_usd
    d["cfp_usd"]=d.cf_usd+d.p_usd
    d["bf_usd"]=d.cfp_usd+d.ac_usd
    d["j_fam_8h"]=d.dias_fam_decl*d.horas_dia_fam/8
    d["w_8h_usd"]=d.jornal_decl_usd*8/d.horas_jornal.where(d.horas_jornal>0)
    d["kc_usd"]=d.j_fam_8h*d.w_8h_usd
    d.loc[d.j_fam_8h==0,"kc_usd"]=0
    d["nip_usd"]=d.cfp_usd-d.kc_usd
    for nombre,den in [("bf_persona_usd","n_hogar"),("bf_ha_usd","area_saf_ha"),("bf_jornal_usd","j_fam_8h")]:
        d[nombre]=d.bf_usd/d[den].where(d[den]>0)
    d["o_usd"]=suma(["o_negocio_usd","o_trab_usd","o_transf_usd"])
    d["h_usd"]=d.cfp_usd+d.o_usd
    d["pm_pct"]=100*d.cfp_usd/d.h_usd.where(d.h_usd>0)
    d["rvc"]=d.gi_usd/(d.cc_usd+d.kc_usd).where(d.cc_usd+d.kc_usd>0)
    d["bf_kext_usd"]=d.bf_usd-d.kext_usd
    d["ni_kext_usd"]=d.nip_usd-d.kext_usd
    d["alim_reduc_si"]=d.alim_reduc_cat.where(d.alim_reduc_cat.isna(),(d.alim_reduc_cat>0).astype(int))
    incierto=(d.pago_inclusion.isin(["NS","NR",""]) | d.pago_inclusion.isna()) & d.pago_cert_decl_usd.notna()
    d["bf_min_pago_usd"]=d.bf_usd
    d["bf_max_pago_usd"]=d.bf_usd
    d.loc[incierto,"bf_min_pago_usd"]=d.cf_usd+d.ac_usd
    d.loc[incierto,"bf_max_pago_usd"]=d.cf_usd+d.ac_usd+d.pago_cert_decl_usd
    return d

def guardar(t,path):
    pd.DataFrame(t).to_csv(path,index=False,encoding="utf-8-sig",float_format="%.10g")

def reporte(out,titulo,md,secciones,notas):
    out=Path(out)
    sim=md.get("tipo_datos")=="SIMULACION"
    marca="SIMULACIÓN FICTICIA — NO ES EVIDENCIA SOBRE PRODUCTORES" if sim else ("PILOTO — ANÁLISIS DESCRIPTIVO" if md.get('etapa')=='PILOTO' else "DATOS DE CAMPO — REVISAR DISEÑO Y COBERTURA")
    partes=[f"<h1>{html.escape(titulo)}</h1><p class='marca'>{marca}</p>",f"<p>Periodo: {html.escape(md.get('periodo_inicio',''))} a {html.escape(md.get('periodo_fin',''))}</p>"]
    for nombre,t in secciones:
        partes.append(f"<h2>{html.escape(nombre)}</h2>")
        partes.append(t.to_html(index=False,float_format=lambda x:f"{x:.4g}",na_rep="No calculable",escape=True) if len(t) else "<p>Sin resultados estimables.</p>")
    partes.append("<h2>Interpretación y límites</h2><ul>"+"".join("<li>"+html.escape(n)+"</li>" for n in notas)+"</ul>")
    css="body{font:15px Arial;max-width:1250px;margin:35px auto;padding:0 20px;color:#222}h1{font-size:26px}h2{font-size:19px;margin-top:30px}table{border-collapse:collapse;font-size:13px;display:block;overflow-x:auto}th{background:#eee;text-align:left}td,th{padding:8px;border-bottom:1px solid #ddd}.marca{font-weight:bold;color:#8b4019}"
    (out/"reporte.html").write_text("<!doctype html><html lang='es'><meta charset='utf-8'><title>"+html.escape(titulo)+"</title><style>"+css+"</style>"+"".join(partes)+"</html>",encoding="utf-8")
    versions={"python":platform.python_version(),"pandas":pd.__version__,"numpy":np.__version__}
    for mod in ("scipy","statsmodels"):
        try: versions[mod]=__import__(mod).__version__
        except ImportError: pass
    (out/"ejecucion.json").write_text(json.dumps({"metadatos":md,"configuracion":config(),"versiones":versions},ensure_ascii=False,indent=2),encoding="utf-8")
