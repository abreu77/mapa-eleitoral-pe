"""Para onde foram os votos: de 2022 (T1 e T2) para 2026, por seção.

Regressão de Goodman sem intercepto, estimada de uma vez para todos os destinos:
cada fração fica entre 0 e 1 e cada origem distribui exatamente 100% dos seus
votos (mínimos quadrados ponderados pelos votos de 2026, com restrição). Grupos
pequenos (outros candidatos) ficam junto com brancos e nulos. Base: votos totais
da seção (sem dado de comparecimento: quem entrou ou saiu do eleitorado votante
não aparece).

Seções usadas: existem nas duas eleições, não são de trânsito, não mudaram de local.
Rodar da raiz do projeto:  python src/transferencia.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RAIZ = Path(__file__).resolve().parents[1]
L = RAIZ / 'dados_limpos'
SAIDA = RAIZ / 'resultados'
CHAVE = ['nr_zona', 'nr_secao']
TIPOS = {'nr_zona': str, 'nr_secao': str, 'nr_votavel': str, 'cd_municipio': str}

votos = pd.read_csv(L / 'votos_secao_longo.csv', dtype=TIPOS)
sec = pd.read_csv(L / 'secoes.csv', dtype=TIPOS)
mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_tse': str})

ok = sec[(sec.eleicao == '2026T1') & (sec.situacao == 'nas_duas') & ~sec.transito & ~sec.mudou_local]
ok = ok.merge(mun[['cd_tse', 'mesorregiao']], left_on='cd_municipio', right_on='cd_tse')
ok['area'] = np.where(ok.mesorregiao == 'Metropolitana de Recife', 'RMR', 'Interior')
ok = ok[CHAVE + ['area']]

GRUPOS = {
    '2022T1': {'77': 'Marília', '45': 'Raquel', '22': 'Anderson', '40': 'Danilo', '44': 'Miguel'},
    '2022T2': {'45': 'Raquel', '77': 'Marília'},
    '2026T1': {'55': 'Raquel', '40': 'João'},
}


def fatias(el):
    v = votos[votos.eleicao == el].copy()
    v['grupo'] = v.nr_votavel.map(GRUPOS[el]).fillna('Outros+branco+nulo')
    t = v.pivot_table(index=CHAVE, columns='grupo', values='qt_votos', aggfunc='sum', fill_value=0)
    total = t.sum(axis=1)
    return t.div(total, axis=0), total


def transicao(origem):
    xo, _ = fatias(origem)
    yd, total26 = fatias('2026T1')
    base = ok.set_index(CHAVE).join(xo, how='inner').join(yd, how='inner', rsuffix='_26')
    base = base.join(total26.rename('peso'))
    orig_cols = list(xo.columns)
    dest_cols = list(yd.columns)
    linhas = []
    for area, d in [('Estado', base)] + list(base.groupby('area')):
        X = d[orig_cols].values
        Y = d[[c + '_26' if c + '_26' in d else c for c in dest_cols]].values
        w = d.peso.values / d.peso.values.sum()
        k, j = X.shape[1], Y.shape[1]

        def custo(b):
            r = X @ b.reshape(k, j) - Y
            return (w[:, None] * r ** 2).sum()

        def grad(b):
            r = X @ b.reshape(k, j) - Y
            return (2 * X.T @ (w[:, None] * r)).ravel()

        cons = [{'type': 'eq', 'fun': (lambda b, i=i: b.reshape(k, j)[i].sum() - 1)} for i in range(k)]
        b0 = np.full(k * j, 1 / j)
        sol = minimize(custo, b0, jac=grad, bounds=[(0, 1)] * (k * j), constraints=cons, method='SLSQP',
                       options={'maxiter': 500, 'ftol': 1e-12})
        assert sol.success, sol.message
        m = pd.DataFrame(sol.x.reshape(k, j), index=orig_cols, columns=dest_cols) * 100
        prev = X @ sol.x.reshape(k, j)
        m.attrs['r2'] = {c: 1 - np.average((Y[:, i] - prev[:, i]) ** 2, weights=w) / np.average((Y[:, i] - np.average(Y[:, i], weights=w)) ** 2, weights=w) for i, c in enumerate(dest_cols)}
        print(f'  {origem} {area}: R² por destino', {c: round(v, 2) for c, v in m.attrs["r2"].items()})
        m['soma'] = m.sum(axis=1)
        # peso de cada origem no total de votos de origem da área
        m['votos_origem_%'] = np.average(X, axis=0, weights=d.peso.values) * 100
        m.insert(0, 'area', area)
        m.insert(1, 'secoes', len(d))
        linhas.append(m)
    return pd.concat(linhas).round(1)


pd.set_option('display.width', 200)
for origem in ['2022T1', '2022T2']:
    r = transicao(origem)
    r.to_csv(SAIDA / f'transferencia_{origem}_2026.csv')
    print(f'\n== De {origem} para 2026: de cada 100 votos do candidato em {origem}, quantos foram para... (estimativa)')
    print(r.to_string())
