"""Incerteza da transferência de votos: bootstrap por município (estado inteiro).

Sorteia municípios com reposição, reestima a matriz e guarda os percentis 5 e 95.
Rodar da raiz do projeto:  python src/transferencia_bootstrap.py
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import transferencia as T

rng = np.random.default_rng(2026)
N = 200


def estima(X, Y, w):
    k, j = X.shape[1], Y.shape[1]
    w = w / w.sum()
    custo = lambda b: (w[:, None] * (X @ b.reshape(k, j) - Y) ** 2).sum()
    grad = lambda b: (2 * X.T @ (w[:, None] * (X @ b.reshape(k, j) - Y))).ravel()
    cons = [{'type': 'eq', 'fun': (lambda b, i=i: b.reshape(k, j)[i].sum() - 1)} for i in range(k)]
    s = minimize(custo, np.full(k * j, 1 / j), jac=grad, bounds=[(0, 1)] * (k * j), constraints=cons,
                 method='SLSQP', options={'maxiter': 500, 'ftol': 1e-12})
    return s.x.reshape(k, j) if s.success else None


sec = T.sec[T.sec.eleicao == '2026T1'][T.CHAVE + ['cd_municipio']]
for origem in ['2022T2', '2022T1']:
    xo, _ = T.fatias(origem)
    yd, total26 = T.fatias('2026T1')
    base = T.ok.set_index(T.CHAVE).join(xo, how='inner').join(yd, rsuffix='_26', how='inner')
    base = base.join(total26.rename('peso')).join(sec.set_index(T.CHAVE)).reset_index()
    oc, dc = list(xo.columns), list(yd.columns)
    ycols = [c + '_26' if c + '_26' in base else c for c in dc]
    grupos = {m: g.index.values for m, g in base.groupby('cd_municipio')}
    muns = np.array(list(grupos))
    amostras = []
    for _ in range(N):
        idx = np.concatenate([grupos[m] for m in rng.choice(muns, len(muns), replace=True)])
        d = base.loc[idx]
        b = estima(d[oc].values, d[ycols].values, d.peso.values)
        if b is not None:
            amostras.append(b * 100)
    a = np.array(amostras)
    ponto = estima(base[oc].values, base[ycols].values, base.peso.values) * 100
    linhas = []
    for i, o in enumerate(oc):
        for jj, de in enumerate(dc):
            linhas.append({'origem': o, 'destino': de, 'estimativa': ponto[i, jj],
                           'p5': np.percentile(a[:, i, jj], 5), 'p95': np.percentile(a[:, i, jj], 95)})
    r = pd.DataFrame(linhas).round(1)
    r.to_csv(T.SAIDA / f'transferencia_{origem}_2026_bootstrap.csv', index=False)
    print(f'\n== {origem} -> 2026, estado, {len(a)} reamostragens por município (faixa p5–p95)')
    r['faixa'] = r.p5.astype(str) + '–' + r.p95.astype(str)
    print(r.pivot(index='origem', columns='destino', values='estimativa').to_string())
    print(r.pivot(index='origem', columns='destino', values='faixa').to_string())
