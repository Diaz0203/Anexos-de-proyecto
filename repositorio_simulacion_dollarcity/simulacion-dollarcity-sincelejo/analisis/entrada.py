import numpy as np, json
from openpyxl import load_workbook
from scipy import stats
wv=load_workbook('../datos/registro_campo_30oct2026.xlsx',data_only=True)
sec=lambda t:t.hour*3600+t.minute*60+t.second
arr=np.array([sec(r[1]) for r in wv['Llegadas'].iter_rows(min_row=6,values_only=True) if r[1] is not None and r[2]!='Sí'],float)
A=[r for r in wv['Atencion'].iter_rows(min_row=6,values_only=True) if r[3] is not None]
ini=np.array([sec(r[3]) for r in A],float);cob=np.array([sec(r[4]) for r in A],float);sal=np.array([sec(r[5]) for r in A],float)
prod=np.array([r[6] for r in A]);tp=np.where(prod==1,1,np.where(prod<=5,2,3))
reg=(cob-ini)/60;emp=(sal-cob)/60;t=(arr-61200)/60
order=np.argsort(ini)
V={}
for k in (1,2,3):
    m=tp==k;o=np.argsort(ini[m])
    V[f'R{k}']=reg[m][o];V[f'E{k}']=emp[m][o];V[f'A{k}']=np.diff(np.sort(t[tp==k]))
def runs_test(x):
    med=np.median(x);s=x[x!=med]>med;n1=s.sum();n2=len(s)-n1;r=1+np.sum(s[1:]!=s[:-1])
    mu=2*n1*n2/(n1+n2)+1;var=2*n1*n2*(2*n1*n2-n1-n2)/((n1+n2)**2*(n1+n2-1));z=(r-mu)/np.sqrt(var)
    return r,z,2*stats.norm.sf(abs(z))
out={}
for k,x in V.items():
    d=dict(n=len(x),media=x.mean(),mediana=np.median(x),de=x.std(ddof=1),min=x.min(),max=x.max(),cv=x.std(ddof=1)/x.mean(),asim=stats.skew(x))
    if k[0] in 'RE':
        p=stats.lognorm.fit(x,floc=0);ks=stats.kstest(x,stats.lognorm.cdf,args=p);d.update(ln_sigma=p[0],ln_med=p[2],ks_D=ks.statistic,ks_p=ks.pvalue)
        pn=stats.norm.fit(x);d['norm_p']=stats.kstest(x,stats.norm.cdf,args=pn).pvalue
        pe=stats.expon.fit(x,floc=0);d['exp_p']=stats.kstest(x,stats.expon.cdf,args=pe).pvalue
        pg=stats.gamma.fit(x,floc=0);d['gam_p']=stats.kstest(x,stats.gamma.cdf,args=pg).pvalue
    else:
        pe=stats.expon.fit(x,floc=0);ks=stats.kstest(x,stats.expon.cdf,args=pe);d.update(ks_D=ks.statistic,ks_p=ks.pvalue)
    r,z,pr=runs_test(x);ac=np.corrcoef(x[:-1],x[1:])[0,1]
    d.update(rachas=int(r),z_r=z,p_r=pr,ac1=ac,lim=2/np.sqrt(len(x)))
    out[k]=d
    print(k,{a:(round(b,3) if isinstance(b,float) else b) for a,b in d.items()})
json.dump({k:{a:float(b) for a,b in d.items()} for k,d in out.items()},open('entrada.json','w'))
json.dump({k:v.tolist() for k,v in V.items()},open('entrada_datos.json','w'))
