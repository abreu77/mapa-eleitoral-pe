"""Robustez do coeficiente da aliança com erro agrupado por microrregião (19 grupos).

1. Erro-padrão agrupado (CR1, correção G/(G-1) e (n-1)/(n-k)), p com t de G-1 graus de liberdade.
2. Wild cluster bootstrap com restrição sob a hipótese nula (coef. da aliança = 0), pesos de Webb
   (6 pontos, indicados para poucos grupos), 9.999 reamostragens. p = fração de |t*| >= |t|.
   Referência do método: Cameron, Gelbach e Miller (2008); Webb (2023) para os pesos.
Modelos: os mesmos de regressao_municipio.py (com e sem efeito fixo de RD; RD e microrregião
são divisões diferentes, então o efeito fixo de RD não absorve o agrupamento).
Rodar da raiz do projeto:  python src/robustez_cluster.py
"""
import contextlib
import io
import runpy
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(RAIZ / 'src/regressao_municipio.py'))
m, MODELOS = g['m'], g['MODELOS']
rng = np.random.default_rng(2026)
B = 9999
WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])


def matriz(df, xs, rd):
    X = df[xs].astype(float)
    if rd:
        X = X.join(pd.get_dummies(df.rd, prefix='rd', drop_first=True, dtype=float))
    X.insert(0, 'const', 1.0)
    return X


def ajusta(X, y, w):
    sw = np.sqrt(w)
    b, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return b


def ep_cluster(X, e, w, grupos):
    n, k = X.shape
    G = len(np.unique(grupos))
    bread = np.linalg.inv(X.T @ (w[:, None] * X))
    meat = np.zeros((k, k))
    for gr in np.unique(grupos):
        s = (X[grupos == gr] * (w * e)[grupos == gr][:, None]).sum(axis=0)
        meat += np.outer(s, s)
    v = bread @ meat @ bread * G / (G - 1) * (n - 1) / (n - k)
    return np.sqrt(np.diag(v)), G


linhas = []
for nome, xs in MODELOS.items():
    for rd in (False, True):
        if nome == 'M1 só aliança' and rd:
            continue
        for peso in (None, 'votos_2026'):
            df = m.dropna(subset=xs + ['raquel_2026T1'])
            Xd = matriz(df, xs, rd)
            X, y = Xd.values, df.raquel_2026T1.values
            w = np.ones(len(df)) if peso is None else df[peso].values / df[peso].mean()
            grupos = df.microrregiao.values
            j = list(Xd.columns).index('aliado_raquel')
            b = ajusta(X, y, w)
            e = y - X @ b
            se, G = ep_cluster(X, e, w, grupos)
            t_obs = b[j] / se[j]
            p_cr1 = 2 * stats.t.sf(abs(t_obs), df=G - 1)
            # bootstrap sob H0: reestima sem a aliança, perturba resíduos por grupo
            X0 = np.delete(X, j, axis=1)
            b0 = ajusta(X0, y, w)
            yhat0, e0 = X0 @ b0, y - X0 @ b0
            gu, gi = np.unique(grupos, return_inverse=True)
            ts = np.empty(B)
            for i in range(B):
                v = rng.choice(WEBB, size=len(gu))[gi]
                ys = yhat0 + e0 * v
                bs = ajusta(X, ys, w)
                ses, _ = ep_cluster(X, ys - X @ bs, w, grupos)
                ts[i] = bs[j] / ses[j]
            p_wild = (np.abs(ts) >= abs(t_obs)).mean()
            linhas.append({'modelo': nome, 'RD': rd, 'peso': 'votos' if peso else 'nenhum', 'n': len(df), 'G': G,
                           'coef': round(b[j], 2), 'ep_cluster': round(se[j], 2), 't': round(t_obs, 2),
                           'p_cluster_tG-1': f'{p_cr1:.1e}', 'p_wild_bootstrap': f'{p_wild:.4f}'})
            print(linhas[-1], flush=True)
r = pd.DataFrame(linhas)
r.to_csv(RAIZ / 'resultados/robustez_cluster.csv', index=False)
print('\n' + r.to_string(index=False))
