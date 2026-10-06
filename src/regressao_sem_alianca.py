"""Transferências sem controlar a aliança: associação total com o voto, e com a própria aliança.

Mesmos dados e controles de regressao_municipio.py (voto de 2022, renda, cota constitucional,
RD), mas sem a variável de aliança. Se a transferência atua através da adesão do prefeito,
a associação dela com o voto aparece aqui e some quando a aliança entra.
Também: aliança ~ transferência + controles (probabilidade linear), para ver se dinheiro e
adesão andam juntos. Tudo descritivo.
Rodar da raiz do projeto:  python src/regressao_sem_alianca.py
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
m, ols = g['m'], g['ols']
CONTROLES = ['raquel_2022T1', 'raquel_2022T2', 'danilo_2022T1', 'log_renda', 'constitucional_2025']
VARS = ['amplo_2025', 'amplo_2023_25', 'capital_2026_ate_jun']

linhas = []
for y in ['raquel_2026T1', 'aliado_raquel']:
    for var in VARS:
        x = m[var].dropna() * 100
        iqr = (np.percentile(x, 75) - np.percentile(x, 25)) / 100
        for com_alianca in ([False, True] if y == 'raquel_2026T1' else [False]):
            xs = CONTROLES + [var] + (['aliado_raquel'] if com_alianca else [])
            for rd in (False, True):
                for peso in (None, 'votos_2026'):
                    t, r2, n = ols(m, y, xs, rd=rd, peso=peso)
                    b, se = t.loc[var, 'coef'], t.loc[var, 'ep_robusto']
                    q = stats.t.ppf(0.975, n - len(t))
                    esc = iqr * (100 if y == 'aliado_raquel' else 1)   # aliança em pontos de probabilidade
                    linhas.append({'y': y, 'transf': var, 'com_alianca': com_alianca, 'RD': rd,
                                   'peso': 'votos' if peso else 'nenhum', 'n': n,
                                   'p25_p75': b * esc, 'ic_inf': (b - q * se) * esc, 'ic_sup': (b + q * se) * esc,
                                   'p': t.loc[var, 'p']})
r = pd.DataFrame(linhas)
r.to_csv(RAIZ / 'resultados/regressao_sem_alianca.csv', index=False)
pd.set_option('display.width', 200)
fmt = lambda d: d.assign(efeito=d.p25_p75.round(2), IC95=d.ic_inf.round(2).astype(str) + ' a ' + d.ic_sup.round(2).astype(str),
                         p=d.p.map(lambda v: f'{v:.3f}'))[['transf', 'com_alianca', 'RD', 'peso', 'n', 'efeito', 'IC95', 'p']]
print('== Voto de Raquel 2026 (p.p.), município no p25 x p75 de transferência por habitante')
print(fmt(r[r.y == 'raquel_2026T1']).to_string(index=False))
print('\n== Probabilidade de o prefeito ser aliado de Raquel (pontos percentuais), p25 x p75 de transferência')
print(fmt(r[r.y == 'aliado_raquel']).to_string(index=False))
