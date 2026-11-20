import numpy as np, heapq
from openpyxl import load_workbook
wv=load_workbook('../datos/registro_campo_30oct2026.xlsx',data_only=True)
sec=lambda t:t.hour*3600+t.minute*60+t.second
arr=np.array([sec(r[1]) for r in wv['Llegadas'].iter_rows(min_row=6,values_only=True) if r[1] is not None and r[2]!='Sí'],float)
prod=np.array([r[6] for r in wv['Atencion'].iter_rows(min_row=6,values_only=True) if r[3] is not None])
tipo=np.where(prod==1,1,np.where(prod<=5,2,3));t=(arr-61200)/60;n=len(t)
P={1:(.538,.175,-.026,.268),2:(.755,.193,.312,.206),3:(1.293,.226,.832,.244)}
def run(rng,th=(6,15,None),t5=None,pack=None):
    svc=[(np.exp(rng.normal(P[k][0],P[k][1])),np.exp(rng.normal(P[k][2],P[k][3]))) for k in tipo]
    INF=1e9;free=[0.,0.,INF,INF,INF];opened=[True,True,False,False,False]
    if t5 is not None: free[4]=t5;opened[4]=True
    ev=[];i=0;nxt=0;W=[];ate=0;hc=[None]*5
    while i<n:
        j=min(range(5),key=lambda k:free[k]);tf=free[j]
        if nxt<n and (t[nxt]<=max(tf,t[i] if i<nxt else 0) or nxt<=i):
            ta=t[nxt];nxt+=1;ql=nxt-i
            for k,thr in ((2,th[0]),(3,th[1]),(4,th[2])):
                if thr is not None and not opened[k] and ql>=thr: opened[k]=True;free[k]=ta;hc[k]=ta
            continue
        s=max(tf,t[i]);r,e=svc[i]
        occ=.16+r+(0.5 if pack else e);fin=s+.16+r+e+(0.5 if pack else 0)
        W.append(s+.16-t[i]);free[j]=s+occ;ate+=fin<=180;i+=1
    return np.mean(W),max(W),ate
def rep(N=300,**kw):
    rng=np.random.default_rng(11);D=np.array([run(rng,**kw) for _ in range(N)]);return D.mean(0).round(2)
if __name__=='__main__':
    print('base',rep())
    for th in [(3,8,None),(4,10,None),(3,6,None),(6,10,None)]: print('umbral',th,rep(th=th))
    for th in [(6,15,20),(6,15,25),(6,15,18)]: print('caja5 umbral',th,rep(th=th))
    print('caja5 18:00',rep(t5=60))
    print('empaque',rep(pack=True))
