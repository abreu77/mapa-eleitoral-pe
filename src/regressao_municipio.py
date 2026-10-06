"""Regressão por município (descritiva): voto de Raquel em 2026 e aliança do prefeito.

Y = % de Raquel nos votos totais de 2026. Controles: voto de Raquel em 2022 (T1 e T2),
voto de Danilo (PSB) em 2022 T1, log da renda mediana per capita (Censo 2022) e RD.
Mínimos quadrados, com e sem peso pelos votos de 2026; erro-padrão robusto (HC1).
Associação, não efeito causal: a aliança pode seguir o favoritismo (Novaes 2018).
Fernando de Noronha fica fora (não tem prefeito).
Rodar da raiz do projeto:  python src/regressao_municipio.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
L, R = RAIZ / 'dados_limpos', RAIZ / 'resultados'

sec = pd.read_csv(L / 'secoes.csv', dtype={'cd_municipio': str})
lon = pd.read_csv(L / 'votos_secao_longo.csv', dtype={'cd_municipio': str, 'nr_votavel': str})
mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_tse': str, 'cd_ibge': str})

g = sec.groupby(['cd_municipio', 'eleicao'])[['raquel', 'total']].sum()
pct = (g.raquel / g.total * 100).unstack()
pct.columns = [f'raquel_{c}' for c in pct.columns]
tot = g.total.unstack()['2026T1'].rename('votos_2026')
dan = lon[(lon.eleicao == '2022T1')].groupby('cd_municipio').apply(
    lambda d: d.loc[d.nr_votavel == '40', 'qt_votos'].sum() / d.qt_votos.sum() * 100, include_groups=False).rename('danilo_2022T1')
m = mun.set_index('cd_tse').join([pct, tot, dan])
m = m[m.alianca_prefeito != 'sem prefeito'].copy()

# transferências do governo do estado (SICONFI), em R$ 100 por habitante
tr = pd.read_csv(L / 'transferencias_estaduais.csv', dtype={'cd_ibge': str, 'ano': str})
pv = tr.pivot_table(index='cd_ibge', columns='ano', values=['amplo', 'capital', 'constitucional', 'pop'], aggfunc='first')
popm = pv['pop']['2025']
transf = pd.DataFrame({
    'amplo_2025': pv['amplo']['2025'] / popm / 100,
    'amplo_2023_25': pv['amplo'][['2023', '2024', '2025']].sum(axis=1) / popm / 100,
    'capital_2026_ate_jun': pv['capital']['2026_ate_b3'] / popm / 100,
    'constitucional_2025': pv['constitucional']['2025'] / popm / 100,
})
m = m.join(transf, on='cd_ibge')
m['aliado_raquel'] = (m.alianca_prefeito == 'Raquel Lyra').astype(int)
m['log_renda'] = np.log(m.renda_pc_mediana)


def ols(df, y, xs, rd=True, peso=None):
    df = df.dropna(subset=xs + [y])   # cada modelo usa só municípios com dado completo
    X = df[xs].astype(float)
    if rd:
        X = X.join(pd.get_dummies(df.rd, prefix='rd', drop_first=True, dtype=float))
    X.insert(0, 'const', 1.0)
    w = np.ones(len(df)) if peso is None else df[peso].values / df[peso].mean()
    Xv, yv = X.values, df[y].values
    sw = np.sqrt(w)
    b, *_ = np.linalg.lstsq(Xv * sw[:, None], yv * sw, rcond=None)
    e = yv - Xv @ b
    n, k = Xv.shape
    bread = np.linalg.inv(Xv.T @ (w[:, None] * Xv))
    meat = (Xv * (w * e)[:, None]).T @ (Xv * (w * e)[:, None])
    se = np.sqrt(np.diag(bread @ meat @ bread) * n / (n - k))
    r2 = 1 - np.average(e ** 2, weights=w) / np.average((yv - np.average(yv, weights=w)) ** 2, weights=w)
    tt = b / se
    pv = 2 * stats.t.sf(np.abs(tt), df=n - k)   # bicaudal, t de Student com n - k graus de liberdade
    out = pd.DataFrame({'coef': b, 'ep_robusto': se, 't': tt, 'p': pv}, index=X.columns)
    return out, r2, n


print('Médias simples por aliança do prefeito (municípios):')
print(m.groupby('alianca_prefeito')[['raquel_2022T1', 'raquel_2022T2', 'raquel_2026T1', 'danilo_2022T1', 'renda_pc_mediana']]
      .mean().round(1).assign(municipios=m.groupby('alianca_prefeito').size()).to_string())

MODELOS = {
    'M1 só aliança': ['aliado_raquel'],
    'M2 + voto 2022': ['aliado_raquel', 'raquel_2022T1', 'raquel_2022T2', 'danilo_2022T1'],
    'M3 + renda': ['aliado_raquel', 'raquel_2022T1', 'raquel_2022T2', 'danilo_2022T1', 'log_renda'],
}
BASE = MODELOS['M3 + renda'] + ['constitucional_2025']
MODELOS.update({
    'M4 + transf. 2025': BASE + ['amplo_2025'],
    'M5 + transf. 2023-25': BASE + ['amplo_2023_25'],
    'M6 + capital 2026 (até jun)': BASE + ['capital_2026_ate_jun'],
})
TRANSF = ['amplo_2025', 'amplo_2023_25', 'capital_2026_ate_jun', 'constitucional_2025']
linhas = []
for nome, xs in MODELOS.items():
    for rd in (False, True):
        for peso in (None, 'votos_2026'):
            if nome == 'M1 só aliança' and rd:
                continue
            t, r2, n = ols(m, 'raquel_2026T1', xs, rd=rd, peso=peso)
            a = t.loc['aliado_raquel']
            linha = {'modelo': nome, 'efeito_fixo_RD': rd, 'peso': 'votos 2026' if peso else 'nenhum',
                     'coef_aliado_pp': a.coef, 'ep': a.ep_robusto, 't': a.t, 'p': a.p, 'r2': r2, 'n': n, 'gl': n - len(t)}
            for v in TRANSF:
                if v in t.index and v != 'constitucional_2025':
                    linha.update({'transf_var': v, 'coef_transf_pp_por_100': t.loc[v, 'coef'], 'p_transf': t.loc[v, 'p']})
            linhas.append(linha)
            if nome == 'M3 + renda' and rd and peso is None:
                print('\nM3 completo, efeito fixo de RD, sem peso:')
                print(t[~t.index.str.startswith('rd_')].round(3).to_string())
res = pd.DataFrame(linhas)
res['p'] = res.p.map(lambda x: f'{x:.1e}')
res['p_transf'] = res.p_transf.map(lambda x: f'{x:.3f}' if pd.notna(x) else '')
print('\nTransferências por habitante (R$), mediana por aliança do prefeito:')
print((m.groupby('alianca_prefeito')[TRANSF].median() * 100).round(0).to_string())
res = res.round(3)
res.to_csv(R / 'regressao_municipio.csv', index=False)
print('\nCoeficiente de "prefeito aliado de Raquel" (pontos percentuais no voto de Raquel em 2026):')
print(res.to_string(index=False))
