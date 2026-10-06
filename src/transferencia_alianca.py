"""Transferência de votos 2022 -> 2026 com abstenção, separada pela aliança do prefeito.

Base: eleitorado apto da seção (abstenção vira categoria nas duas eleições).
Regressão de Goodman com restrição (cada origem distribui 100%), estimada à parte
para municípios de prefeito aliado de Raquel e de prefeito aliado de João.
Incerteza: 200 reamostragens de municípios dentro de cada grupo (faixa p5–p95).

Seções usadas: existem nas duas eleições, não são de trânsito, não mudaram de local.
Não modela entrada e saída do eleitorado (novos eleitores, óbitos, transferências).
Rodar da raiz do projeto:  python src/transferencia_alianca.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RAIZ = Path(__file__).resolve().parents[1]
L, SAIDA = RAIZ / 'dados_limpos', RAIZ / 'resultados'
CHAVE = ['nr_zona', 'nr_secao']
TIPOS = {'nr_zona': str, 'nr_secao': str, 'nr_votavel': str, 'cd_municipio': str}
N_BOOT = 200
rng = np.random.default_rng(2026)

votos = pd.read_csv(L / 'votos_secao_longo.csv', dtype=TIPOS)
sec = pd.read_csv(L / 'secoes.csv', dtype=TIPOS)
mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_tse': str})

GRUPOS = {
    '2022T1': {'77': 'Marília', '45': 'Raquel', '22': 'Anderson', '40': 'Danilo', '44': 'Miguel'},
    '2022T2': {'45': 'Raquel', '77': 'Marília'},
    '2026T1': {'55': 'Raquel', '40': 'João'},
}


def fatias(el):
    """Fração do eleitorado apto de cada seção em cada opção, abstenção incluída."""
    v = votos[votos.eleicao == el].copy()
    v['grupo'] = v.nr_votavel.map(GRUPOS[el]).fillna('Outros+branco+nulo')
    t = v.pivot_table(index=CHAVE, columns='grupo', values='qt_votos', aggfunc='sum', fill_value=0)
    s = sec[sec.eleicao == el].set_index(CHAVE)
    t['Abstenção'] = s.abstencoes
    aptos = s.aptos.reindex(t.index)
    return t.div(aptos, axis=0), aptos


def estima(X, Y, w):
    k, j = X.shape[1], Y.shape[1]
    w = w / w.sum()
    custo = lambda b: (w[:, None] * (X @ b.reshape(k, j) - Y) ** 2).sum()
    grad = lambda b: (2 * X.T @ (w[:, None] * (X @ b.reshape(k, j) - Y))).ravel()
    cons = [{'type': 'eq', 'fun': (lambda b, i=i: b.reshape(k, j)[i].sum() - 1)} for i in range(k)]
    s = minimize(custo, np.full(k * j, 1 / j), jac=grad, bounds=[(0, 1)] * (k * j), constraints=cons,
                 method='SLSQP', options={'maxiter': 1000, 'ftol': 1e-12})
    return s.x.reshape(k, j) if s.success else None


base26 = sec[(sec.eleicao == '2026T1') & (sec.situacao == 'nas_duas') & ~sec.transito & ~sec.mudou_local]
base26 = base26.merge(mun[['cd_tse', 'alianca_prefeito']], left_on='cd_municipio', right_on='cd_tse')
base26 = base26.set_index(CHAVE)[['cd_municipio', 'alianca_prefeito']]
base26 = base26[base26.alianca_prefeito != 'sem prefeito']

pd.set_option('display.width', 220)
todas = []
for origem in ['2022T2', '2022T1']:
    xo, _ = fatias(origem)
    yd, aptos26 = fatias('2026T1')
    d0 = base26.join(xo, how='inner').join(yd, how='inner', rsuffix='_26').join(aptos26.rename('peso'))
    d0 = d0.dropna()
    oc, dc = list(xo.columns), list(yd.columns)
    yc = [c + '_26' if c + '_26' in d0 else c for c in dc]
    for grupo, d in [('Estado', d0)] + [(f'Prefeito com {g}', x) for g, x in d0.groupby('alianca_prefeito')]:
        ponto = estima(d[oc].values, d[yc].values, d.peso.values) * 100
        idx_mun = {m: np.flatnonzero(d.cd_municipio.values == m) for m in d.cd_municipio.unique()}
        muns = np.array(list(idx_mun))
        boot = []
        for _ in range(N_BOOT):
            ii = np.concatenate([idx_mun[m] for m in rng.choice(muns, len(muns), replace=True)])
            b = estima(d[oc].values[ii], d[yc].values[ii], d.peso.values[ii])
            if b is not None:
                boot.append(b * 100)
        boot = np.array(boot)
        prev = d[oc].values @ (ponto / 100)
        w = d.peso.values / d.peso.values.sum()
        r2 = {c: 1 - np.average((d[yc[i]] - prev[:, i]) ** 2, weights=w) /
              np.average((d[yc[i]] - np.average(d[yc[i]], weights=w)) ** 2, weights=w) for i, c in enumerate(dc)}
        for i, o in enumerate(oc):
            for jj, de in enumerate(dc):
                todas.append({'origem_eleicao': origem, 'grupo': grupo, 'municipios': len(muns), 'secoes': len(d),
                              'origem': o, 'destino': de, 'estimativa': ponto[i, jj],
                              'p5': np.percentile(boot[:, i, jj], 5), 'p95': np.percentile(boot[:, i, jj], 95),
                              'peso_origem_%': np.average(d[o], weights=d.peso) * 100, 'r2_destino': r2[de]})
        print(f'{origem} | {grupo}: {len(muns)} municípios, {len(d)} seções, {len(boot)} reamostragens; '
              f'R² ' + ', '.join(f'{c} {v:.2f}' for c, v in r2.items()))

res = pd.DataFrame(todas).round(2)
res.to_csv(SAIDA / 'transferencia_alianca.csv', index=False)
for origem in ['2022T2', '2022T1']:
    r = res[res.origem_eleicao == origem].copy()
    r['txt'] = r.estimativa.round(0).astype(int).astype(str) + ' (' + r.p5.round(0).astype(int).astype(str) + '–' + \
        r.p95.round(0).astype(int).astype(str) + ')'
    print(f'\n== De {origem} para 2026: de cada 100 eleitores aptos de cada origem, quantos foram para... ')
    print(r.pivot_table(index=['grupo', 'origem'], columns='destino', values='txt', aggfunc='first').to_string())
