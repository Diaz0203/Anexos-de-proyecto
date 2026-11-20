import pandas as pd, numpy as np, json, itertools
from scipy import stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

d = pd.read_csv('../resultados/factorial_576_corridas.csv')
d['E'] = d.esc.str.replace('Escenario ', 'E').str.strip()
d['FA'] = d.Regla.astype(int); d['FB'] = d.Caja5.astype(int); d['FC'] = d.Empaque.astype(int)
NOM = {'E1': 'Base', 'E2': 'Empaque', 'E3': 'Caja 5', 'E4': 'Caja 5 + Empaque', 'E5': 'Regla',
       'E6': 'Regla + Empaque', 'E7': 'Regla + Caja 5', 'E8': 'Las tres'}
R = {}
RESP = ['EsperaPromedio', 'EsperaMaxima', 'AtendidosAntes20']

# --- verification ---
ver = {}
ver['clientes_172_todas'] = bool((d.ClientesTotales == 172).all())
ver['caja5_abre_solo_con_B2'] = {
    'B1_abre': int(((d.FB == 1) & (d.AperturaCaja5 > 0)).sum()),
    'B2_abre': int(((d.FB == 2) & (d.AperturaCaja5 > 0)).sum()),
    'B2_total': int((d.FB == 2).sum()),
    'por_esc': d[d.FB == 2].groupby('E').AperturaCaja5.apply(lambda x: int((x > 0).sum())).to_dict()}
w = d.pivot(index='rep', columns='E', values='EsperaPromedio')
iguales = sum(int((w[a] == w[b]).sum()) for a, b in itertools.combinations(w.columns, 2))
cors = {f'{a}-{b}': round(stats.pearsonr(w[a], w[b])[0], 3) for a, b in itertools.combinations(w.columns, 2)}
ver['indep'] = {'pares_iguales': iguales, 'n_comparaciones': 28 * 72,
                'r_min': min(cors.values()), 'r_max': max(cors.values()),
                'limite': round(1.96 / np.sqrt(72), 3),
                'fuera': [k for k, v in cors.items() if abs(v) > 1.96 / np.sqrt(72)], 'cors': cors}
# runs test / lag-1 by replication order inside each scenario
lag = {e: round(pd.Series(w[e].values).autocorr(1), 3) for e in w.columns}
ver['lag1_por_esc'] = lag
R['verificacion'] = ver

# --- descriptive ---
desc = {}
for y in RESP + ['AperturaCaja3', 'AperturaCaja4']:
    g = d.groupby('E')[y]
    m, s = g.mean(), g.std()
    h = stats.t.ppf(0.975, 71) * s / np.sqrt(72)
    desc[y] = {e: dict(media=round(m[e], 3), de=round(s[e], 3), li=round(m[e] - h[e], 3), ls=round(m[e] + h[e], 3),
                       min=round(g.min()[e], 2), max=round(g.max()[e], 2)) for e in m.index}
R['desc'] = desc
R['caja5_aperturas'] = {e: dict(n=int((x > 0).sum()), media=round(x[x > 0].mean(), 2) if (x > 0).any() else None)
                        for e, x in d.groupby('E').AperturaCaja5}

# --- ANOVA ---
def anova(y, data, trans=None):
    dd = data.copy()
    dd['y'] = np.log(dd[y]) if trans == 'log' else dd[y]
    mod = smf.ols('y ~ C(FA, Sum)*C(FB, Sum)*C(FC, Sum)', data=dd).fit()
    t = sm.stats.anova_lm(mod, typ=3).drop('Intercept')
    sse = t.loc['Residual', 'sum_sq']
    out = {}
    names = {'C(FA, Sum)': 'A', 'C(FB, Sum)': 'B', 'C(FC, Sum)': 'C', 'C(FA, Sum):C(FB, Sum)': 'AxB',
             'C(FA, Sum):C(FC, Sum)': 'AxC', 'C(FB, Sum):C(FC, Sum)': 'BxC',
             'C(FA, Sum):C(FB, Sum):C(FC, Sum)': 'AxBxC', 'Residual': 'Error'}
    for k, r in t.iterrows():
        n = names[k]
        out[n] = dict(gl=int(r.df), SC=round(r.sum_sq, 3), CM=round(r.sum_sq / r.df, 4),
                      F=None if n == 'Error' else round(r.F, 2),
                      p=None if n == 'Error' else float(r['PR(>F)']),
                      eta2p=None if n == 'Error' else round(r.sum_sq / (r.sum_sq + sse), 3))
    res = mod.resid
    sh = stats.shapiro(res)
    lev = stats.levene(*[g.y.values for _, g in dd.groupby('E')], center='median')
    return out, dict(shapiro_W=round(sh.statistic, 4), shapiro_p=float(sh.pvalue),
                     levene_F=round(lev.statistic, 3), levene_p=float(lev.pvalue),
                     R2=round(mod.rsquared, 4)), mod

R['anova'] = {}; R['supuestos'] = {}; R['anova_log'] = {}; R['supuestos_log'] = {}
mods = {}
for y in RESP:
    a, s, mods[y] = anova(y, d)
    R['anova'][y] = a; R['supuestos'][y] = s
    a2, s2, _ = anova(y, d, 'log')
    R['anova_log'][y] = a2; R['supuestos_log'][y] = s2

# Kruskal per factor and across scenarios
R['kruskal'] = {}
for y in RESP:
    kk = {}
    for f in ['FA', 'FB', 'FC']:
        k = stats.kruskal(*[g[y].values for _, g in d.groupby(f)]); kk[f] = dict(H=round(k.statistic, 2), p=float(k.pvalue))
    k = stats.kruskal(*[g[y].values for _, g in d.groupby('E')]); kk['esc'] = dict(H=round(k.statistic, 2), p=float(k.pvalue))
    R['kruskal'][y] = kk

# --- effects (means by level, two-way tables) ---
eff = {}
for y in RESP:
    eff[y] = {f: d.groupby(f)[y].mean().round(3).to_dict() for f in ['FA', 'FB', 'FC']}
    eff[y]['AB'] = {f'{a}{b}': round(v, 3) for (a, b), v in d.groupby(['FA', 'FB'])[y].mean().items()}
    eff[y]['AC'] = {f'{a}{c}': round(v, 3) for (a, c), v in d.groupby(['FA', 'FC'])[y].mean().items()}
    eff[y]['BC'] = {f'{b}{c}': round(v, 3) for (b, c), v in d.groupby(['FB', 'FC'])[y].mean().items()}
R['efectos'] = eff

# --- Tukey on 8 scenarios (all interactions significant -> compare cells) + Games-Howell check
R['tukey'] = {}
for y in RESP:
    tk = pairwise_tukeyhsd(d[y], d.E)
    tab = pd.DataFrame(tk._results_table.data[1:], columns=tk._results_table.data[0])
    R['tukey'][y] = [dict(a=r.group1, b=r.group2, dif=round(r.meandiff, 3), li=round(r.lower, 3), ls=round(r.upper, 3),
                          p=float(r['p-adj']), rej=bool(r.reject)) for _, r in tab.iterrows()]

def games_howell(y):
    out = []
    g = {e: x[y].values for e, x in d.groupby('E')}
    k = len(g)
    for a, b in itertools.combinations(sorted(g), 2):
        xa, xb = g[a], g[b]; na, nb = len(xa), len(xb)
        va, vb = xa.var(ddof=1) / na, xb.var(ddof=1) / nb
        se = np.sqrt(va + vb); dif = xb.mean() - xa.mean()
        df = (va + vb) ** 2 / (va ** 2 / (na - 1) + vb ** 2 / (nb - 1))
        q = abs(dif) / se * np.sqrt(2)
        p = float(stats.studentized_range.sf(q, k, df))
        out.append(dict(a=a, b=b, dif=round(dif, 3), p=p, rej=p < 0.05))
    return out
R['games_howell'] = {y: games_howell(y) for y in RESP}

# --- simple effects: each factor within each combination of the other two (Welch t, Bonferroni 12)
se = {}
for y in RESP:
    L = []
    for f, others in [('FA', ['FB', 'FC']), ('FB', ['FA', 'FC']), ('FC', ['FA', 'FB'])]:
        for (o1, o2), g in d.groupby(others):
            x1 = g[g[f] == 1][y]; x2 = g[g[f] == 2][y]
            t = stats.ttest_ind(x2, x1, equal_var=False)
            L.append(dict(factor=f, en=f'{others[0]}={o1},{others[1]}={o2}', m1=round(x1.mean(), 3), m2=round(x2.mean(), 3),
                          dif=round(x2.mean() - x1.mean(), 3), p_bonf=min(1, float(t.pvalue) * 12)))
    se[y] = L
R['efectos_simples'] = se

# --- Dunnett vs E1
R['dunnett'] = {}
for y in RESP:
    base = d[d.E == 'E1'][y].values
    otros = [d[d.E == e][y].values for e in ['E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8']]
    dn = stats.dunnett(*otros, control=base)
    ci = dn.confidence_interval()
    R['dunnett'][y] = {e: dict(dif=round(o.mean() - base.mean(), 3), li=round(ci.low[i], 3), ls=round(ci.high[i], 3),
                               p=float(dn.pvalue[i]), pct=round(100 * (o.mean() - base.mean()) / base.mean(), 1))
                       for i, (e, o) in enumerate(zip(['E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8'], otros))}

# --- validation of base against real data (Z test, like before)
b = d[d.E == 'E1'].EsperaPromedio
real_m, real_v, real_n = 16.43, 53.47, 172
z = (b.mean() - real_m) / np.sqrt(b.var(ddof=1) / 72 + real_v / real_n)
R['validacion_base'] = dict(media=round(b.mean(), 3), var=round(b.var(ddof=1), 3), Z=round(z, 3), p=float(2 * stats.norm.sf(abs(z))))
json.dump(R, open('factorial_res.json', 'w'), indent=1, ensure_ascii=False, default=float)

# print summary
for y in RESP:
    print('\n==', y)
    for k, v in R['anova'][y].items(): print(f"{k:6} gl={v['gl']:3} F={v['F']} p={v['p']} eta2p={v['eta2p']}")
    print('sup', R['supuestos'][y], '\nlog', R['supuestos_log'][y])
    print('log ANOVA p:', {k: (v['p'], v['eta2p']) for k, v in R['anova_log'][y].items() if k != 'Error'})
    print('KW', R['kruskal'][y])
    print('Dunnett', R['dunnett'][y])
    ns = [(t['a'], t['b'], t['dif'], round(t['p'], 3)) for t in R['tukey'][y] if not t['rej']]
    print('Tukey no sig:', ns)
    print('GH no sig:', [(t['a'], t['b'], t['dif'], round(t['p'], 3)) for t in R['games_howell'][y] if not t['rej']])
    print('simple ns:', [(t['factor'], t['en'], t['dif'], round(t['p_bonf'], 3)) for t in R['efectos_simples'][y] if t['p_bonf'] >= 0.05])
print(json.dumps({k: v for k, v in R['verificacion'].items() if k != 'indep'}, indent=0))
print({k: v for k, v in R['verificacion']['indep'].items() if k != 'cors'})
print(R['validacion_base'], R['caja5_aperturas'])
