"""Comparación C1 frente a C0. Uso: python analisis_doctoral.py entrada.xlsx --salida carpeta"""
from pathlib import Path
import sys, argparse, itertools
sys.path.insert(0,str(Path(__file__).resolve().parent/"_deps_prueba"))
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.oneway import anova_oneway
from comun import cargar, guardar, reporte, config, ErrorDatos

ECON=["bf_usd","cfp_usd","ac_usd","nip_usd","bf_persona_usd","bf_ha_usd","bf_jornal_usd","pm_pct","cc_usd"]
UNIDADES={c:"USD/hogar/año" for c in ECON+["bf_kext_usd","bf_min_pago_usd","bf_max_pago_usd"]}
UNIDADES.update(bf_persona_usd="USD/persona/año",bf_ha_usd="USD/ha SAF/año",bf_jornal_usd="USD/jornada familiar 8 h",pm_pct="puntos porcentuales para diferencias",area_saf_ha="ha SAF",n_hogar="personas/hogar",j_fam_8h="jornadas de 8 h/hogar/año")

def welch(d,c,permitido=True):
    x=d.loc[d.grupo_cert=="C1",c].dropna().to_numpy(float)
    y=d.loc[d.grupo_cert=="C0",c].dropna().to_numpy(float)
    r=dict(variable=c,unidad=UNIDADES.get(c,"índice adimensional 0–1"),n_C0=len(y),n_C1=len(x),media_C0=np.mean(y) if len(y) else np.nan,
           media_C1=np.mean(x) if len(x) else np.nan,diferencia_C1_C0=np.nan,ic95_inf=np.nan,ic95_sup=np.nan,
           t=np.nan,gl=np.nan,p=np.nan,estado="No estimable")
    if len(x) and len(y): r["diferencia_C1_C0"]=float(x.mean()-y.mean())
    if not permitido: r["estado"]="Solo descripción: diseño no habilita inferencia simple"; return r
    if min(len(x),len(y))<2: return r
    a=x.var(ddof=1)/len(x); b=y.var(ddof=1)/len(y)
    if a+b<=0: r["estado"]="Varianza nula en ambos grupos"; return r
    gl=(a+b)**2/(a*a/(len(x)-1)+b*b/(len(y)-1)); se=np.sqrt(a+b)
    t=r["diferencia_C1_C0"]/se; p=2*stats.t.sf(abs(t),gl); q=stats.t.ppf(.975,gl)
    r.update(ic95_inf=r["diferencia_C1_C0"]-q*se,ic95_sup=r["diferencia_C1_C0"]+q*se,t=t,gl=gl,p=p,estado="Welch bilateral")
    return r

def holm(t,col="p",dest="p_holm",mask=None):
    t=t.copy(); t[dest]=np.nan
    ok=t[col].notna() if mask is None else t[col].notna()&mask
    if ok.any(): t.loc[ok,dest]=multipletests(t.loc[ok,col],method="holm")[1]
    return t

def wilson(k,n):
    z=stats.norm.ppf(.975); p=k/n; a=1+z*z/n
    centro=(p+z*z/(2*n))/a
    h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/a
    return centro-h,centro+h

def sociales(d,permitido):
    resultados=[]; frecuencias=[]; cfg=config()
    campos=["alim_reduc_si","salud_acceso","escuela_asist","transp_dific","decision_part","satisf_saf","registro_econ","apoyo_aplicado"]
    for c in campos:
        sub=d[d.grupo_cert.isin(["C0","C1"]) & d[c].notna()]
        tab=pd.crosstab(sub.grupo_cert,sub[c]).reindex(["C0","C1"],fill_value=0)
        for g in ("C0","C1"):
            total=int(tab.loc[g].sum())
            for cat in tab.columns:
                k=int(tab.loc[g,cat]); frecuencias.append(dict(variable=c,grupo=g,categoria=cat,n=k,denominador=total,porcentaje=100*k/total if total else np.nan))
        r=dict(variable=c,n_C0=int(tab.loc["C0"].sum()),n_C1=int(tab.loc["C1"].sum()),prueba="No estimable",estadistico=np.nan,p=np.nan,
               diferencia_pp=np.nan,ic95_inf_pp=np.nan,ic95_sup_pp=np.nan,theta_C1_C0=np.nan,r_biserial=np.nan,replicas_MC=np.nan,error_MC_aprox=np.nan)
        if min(r["n_C0"],r["n_C1"])==0: resultados.append(r); continue
        if c=="alim_reduc_si":
            k1=int(tab.loc["C1"].get(1,0)); k0=int(tab.loc["C0"].get(1,0)); n1=r["n_C1"]; n0=r["n_C0"]
            p1=k1/n1; p0=k0/n0; dif=p1-p0; r["diferencia_pp"]=100*dif
            if permitido:
                l1,u1=wilson(k1,n1); l0,u0=wilson(k0,n0)
                r.update(ic95_inf_pp=100*(dif-np.sqrt((p1-l1)**2+(u0-p0)**2)),ic95_sup_pp=100*(dif+np.sqrt((u1-p1)**2+(p0-l0)**2)))
        if not permitido: r["prueba"]="Solo descripción por diseño"; resultados.append(r); continue
        if c in ("satisf_saf","registro_econ","apoyo_aplicado"):
            x=sub.loc[sub.grupo_cert=="C1",c]; y=sub.loc[sub.grupo_cert=="C0",c]
            z=stats.mannwhitneyu(x,y,alternative="two-sided",method="asymptotic")
            theta=z.statistic/(len(x)*len(y))
            r.update(prueba="Mann–Whitney con empates",estadistico=z.statistic,p=z.pvalue,theta_C1_C0=theta,r_biserial=2*theta-1)
        elif tab.shape[1]<2:
            r["prueba"]="Sin variación de categorías"
        else:
            chi,p,gl,expected=stats.chi2_contingency(tab.to_numpy(),correction=False)
            if (expected<5).any():
                if tab.shape==(2,2):
                    odds,p=stats.fisher_exact(tab.to_numpy(),alternative="two-sided")
                    r.update(prueba="Fisher bilateral",estadistico=odds,p=p)
                else:
                    B=19999
                    # scipy 1.14 (WebAssembly) no ofrece method=MonteCarloMethod.
                    # random_table conserva exactamente los dos márgenes.
                    obs=tab.to_numpy(); rng=np.random.default_rng(cfg["seed"]+campos.index(c))
                    simuladas=stats.random_table.rvs(obs.sum(axis=1),obs.sum(axis=0),size=B,random_state=rng)
                    estad=((simuladas-expected)**2/expected).sum(axis=(1,2))
                    pmc=(1+np.count_nonzero(estad>=chi-1e-12))/(B+1)
                    r.update(prueba="Pearson con Monte Carlo condicional RxC",estadistico=chi,p=pmc,replicas_MC=B,error_MC_aprox=np.sqrt(pmc*(1-pmc)/(B+1)))
            else: r.update(prueba="Chi cuadrado Pearson",estadistico=chi,p=p)
        resultados.append(r)
    return holm(pd.DataFrame(resultados)),pd.DataFrame(frecuencias)

def modelo(d,permitido,cfg):
    columnas=["bf_usd","cert_estable","area_saf_ha","n_hogar"]
    sub=d[d.grupo_cert.isin(["C0","C1"])].dropna(subset=columnas).copy()
    info={"n":len(sub),"estado":"No ajustado","nota":""}; vacio=pd.DataFrame()
    if not permitido: info["nota"]="Diseño no habilitado para inferencia simple"; return vacio,vacio,pd.DataFrame([info])
    ngrupo=sub.groupby("cert_estable").size()
    if len(sub)<cfg["modelo_min_n"] or len(ngrupo)<2 or ngrupo.min()<cfg["modelo_min_grupo"]:
        info["nota"]="No alcanza umbrales operativos configurados; no son una garantía de potencia"; return vacio,vacio,pd.DataFrame([info])
    sub["ln_area"]=np.log(sub.area_saf_ha)
    X=sm.add_constant(sub[["cert_estable","ln_area","n_hogar"]],has_constant="add")
    if np.linalg.matrix_rank(X.to_numpy())<X.shape[1]: info["nota"]="Matriz sin rango completo"; return vacio,vacio,pd.DataFrame([info])
    base=sm.OLS(sub.bf_usd,X).fit(); ajuste=base.get_robustcov_results(cov_type="HC3",use_t=True)
    ci=ajuste.conf_int(); filas=[]
    for i,c in enumerate(X.columns):
        filas.append(dict(termino=c,coeficiente=ajuste.params[i],error_HC3=ajuste.bse[i],ic95_inf=ci[i,0],ic95_sup=ci[i,1],p=ajuste.pvalues[i],unidad="USD/hogar/año por unidad del término"))
    infl=base.get_influence()
    diag=pd.DataFrame({"id_hogar":sub.id_hogar,"predicho":base.fittedvalues,"residuo":base.resid,"cook":infl.cooks_distance[0],"apalancamiento":infl.hat_matrix_diag})
    a=sub[sub.cert_estable==1].area_saf_ha; b=sub[sub.cert_estable==0].area_saf_ha
    info.update(estado="OLS con HC3",r2_ajustado=base.rsquared_adj,n_C0=int(ngrupo.get(0,0)),n_C1=int(ngrupo.get(1,0)),
                area_soporte_inf=max(a.min(),b.min()),area_soporte_sup=min(a.max(),b.max()),condicion_matriz=np.linalg.cond(X.to_numpy()),
                nota="Ajuste por área ACTUAL y miembros; asociación condicionada, no efecto causal")
    return pd.DataFrame(filas),diag,pd.DataFrame([info])

def ejecutar(entrada,salida):
    out=Path(salida); cfg=config(); d,estados,md=cargar(entrada,out)
    permitido=md.get("diseno")=="aleatorio_simple_independiente"
    base=d[d.grupo_cert.isin(["C0","C1"])].copy()
    resumen=[]
    for g,sub in d.groupby("grupo_cert"):
        for c in ECON+["area_saf_ha","n_hogar","j_fam_8h"]:
            x=sub[c].dropna(); resumen.append(dict(grupo=g,variable=c,unidad=UNIDADES[c],n=len(x),faltantes=len(sub)-len(x),media=x.mean(),de=x.std(),mediana=x.median(),p25=x.quantile(.25),p75=x.quantile(.75)))
    resumen=pd.DataFrame(resumen)
    contrastes=pd.DataFrame([welch(base,c,permitido) for c in ECON])
    contrastes=holm(contrastes,mask=contrastes.variable.ne("bf_usd"))
    social,freq=sociales(base,permitido)
    coef,diag,modelo_info=modelo(d,permitido,cfg)
    sens=pd.DataFrame([welch(base,c,permitido) for c in ["cfp_usd","bf_kext_usd","bf_min_pago_usd","bf_max_pago_usd"]])
    boot=[]; rng=np.random.default_rng(cfg["seed"])
    for funcion in [np.mean,np.median]:
        x=base.loc[base.grupo_cert=="C1","bf_usd"].dropna().to_numpy(); y=base.loc[base.grupo_cert=="C0","bf_usd"].dropna().to_numpy()
        if permitido and min(len(x),len(y))>=8:
            reps=[funcion(rng.choice(x,len(x),replace=True))-funcion(rng.choice(y,len(y),replace=True)) for _ in range(cfg["bootstrap_replicas"])]
            li,ls=np.quantile(reps,[.025,.975]); boot.append(dict(estimando=funcion.__name__,replicas=cfg["bootstrap_replicas"],diferencia=funcion(x)-funcion(y),ic95_inf=li,ic95_sup=ls,metodo="Bootstrap percentil complementario"))
    diagnosticos=[]
    for g,sub in base.groupby("grupo_cert"):
        x=sub.bf_usd.dropna()
        if 3<=len(x)<=5000 and x.nunique()>1:
            w,p=stats.shapiro(x); diagnosticos.append(dict(grupo=g,n=len(x),W=w,p=p,uso="Diagnóstico; no selecciona automáticamente prueba"))
    combos=[]; grupos=[(g,s) for g,s in base.groupby("combo_cert") if s.bf_usd.notna().sum()>=8]
    if permitido and len(grupos)>=3:
        z=anova_oneway([s.bf_usd.dropna().to_numpy() for _,s in grupos],use_var="unequal")
        combos.append(dict(comparacion="Global combinaciones con al menos 8 BF válidos",estadistico=z.statistic,p=z.pvalue))
    pares=[]
    if permitido:
        for nombre,s in grupos:
            if nombre=="SIN": continue
            sub=pd.concat([base[base.grupo_cert=="C0"],s]); r=welch(sub,"bf_usd"); r["combinacion"]=nombre; pares.append(r)
    pares=holm(pd.DataFrame(pares)) if pares else pd.DataFrame()
    tablas={"indicadores_hogares":d,"resumen_por_grupo":resumen,"contrastes_economicos":contrastes,"contrastes_sociales":social,
            "frecuencias_sociales":freq,"modelo_HC3":coef,"diagnosticos_modelo":diag,"informacion_modelo":modelo_info,
            "sensibilidad":sens,"bootstrap_BF":pd.DataFrame(boot),"diagnostico_shapiro":pd.DataFrame(diagnosticos),
            "welch_combinaciones":pd.DataFrame(combos),"pares_combinaciones":pares}
    for nombre,t in tablas.items(): guardar(t,out/(nombre+".csv"))
    reporte(out,"Comparación doctoral de certificados y no certificados",md,
            [("Composición de muestra",d.groupby("grupo_cert").size().rename("n").reset_index()),("Comparación económica",contrastes),("Comparación social",social),("Modelo ajustado HC3",coef),("Viabilidad del modelo",modelo_info),("Bootstrap de BF",pd.DataFrame(boot))],
            ["Los resultados de simulación solo verifican el funcionamiento del procedimiento. No describen a Fortaleza del Valle.",
             "C0 y C1 son grupos independientes. C2, C3 y CU no se incluyen en el contraste principal.",
             "Holm económico excluye el BF primario. Holm social incluye los contrastes sociales y de gestión programados.",
             "El ajuste usa superficie actual y tamaño del hogar; no identifica causalidad.",
             "Para tablas dispersas RxC se aproxima el p mediante Monte Carlo condicional con 19.999 réplicas; no se usa la aproximación asintótica de chi cuadrado.",
             "Si el diseño no es aleatorio simple e independiente, el programa entrega descripciones y omite la inferencia simple; requiere adaptar el análisis al diseño."])
    print(f"Doctorado terminado: {out.resolve()}")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("entrada");p.add_argument("--salida",default="resultados_doctoral");a=p.parse_args()
    try: ejecutar(a.entrada,a.salida)
    except ErrorDatos as e: p.exit(2,"Datos no analizables: "+str(e)+"\n")
