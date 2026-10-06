"""Pergunta 1: onde Raquel cresceu ou caiu entre 2022 e 2026, e o perfil dessas áreas.

Métrica: % de Raquel sobre os votos totais (brancos e nulos no denominador).
Variação principal: 2026 T1 menos 2022 T2, em pontos percentuais (p.p.).
Rodar da raiz do projeto:  python src/analise_p1.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
L = RAIZ / 'dados_limpos'
SAIDA = RAIZ / 'resultados'
SAIDA.mkdir(exist_ok=True)
CHAVE = ['nr_zona', 'nr_secao']
TIPOS = {'nr_zona': str, 'nr_secao': str, 'cd_municipio': str}

sec = pd.read_csv(L / 'secoes.csv', dtype=TIPOS)
mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_tse': str, 'cd_ibge': str})
perf = pd.read_csv(L / 'perfil_secao_2026.csv', dtype=TIPOS)
sec = sec.merge(mun[['cd_tse', 'nm_municipio', 'rd', 'mesorregiao']], left_on='cd_municipio', right_on='cd_tse', how='left')


def tabela(nivel):
    """% de Raquel por unidade do nível, nas três eleições, e as variações."""
    g = sec.groupby(nivel + ['eleicao'])[['raquel', 'total']].sum()
    p = (g.raquel / g.total * 100).unstack('eleicao')
    p.columns = [f'pct_{c}' for c in p.columns]
    t = g.total.unstack('eleicao')
    p['votos_2026'] = t['2026T1']
    p['var_vs_2022T2'] = p.pct_2026T1 - p.pct_2022T2
    p['var_vs_2022T1'] = p.pct_2026T1 - p.pct_2022T1
    return p.round(2)


pd.set_option('display.width', 200)
estado = tabela([]) if False else None
g = sec.groupby('eleicao')[['raquel', 'total']].sum()
print('ESTADO, % de Raquel nos votos totais:', (g.raquel / g.total * 100).round(2).to_dict())

for nome, nivel in [('mesorregiao', ['mesorregiao']), ('rd', ['rd']), ('municipio', ['nm_municipio', 'rd'])]:
    t = tabela(nivel)
    t.to_csv(SAIDA / f'p1_{nome}.csv')
    if nome != 'municipio':
        print(f'\n== {nome.upper()}'); print(t.sort_values('var_vs_2022T2').to_string())
    else:
        print('\n== MUNICÍPIOS: distribuição da variação vs 2022 T2 (p.p.)')
        print(t.var_vs_2022T2.describe().round(2).to_string())
        print('cresceu em', (t.var_vs_2022T2 > 0).sum(), 'de', len(t))
        print('\nMaiores quedas:'); print(t.nsmallest(8, 'var_vs_2022T2')[['pct_2022T2', 'pct_2026T1', 'var_vs_2022T2', 'votos_2026']].to_string())
        print('\nMaiores altas:'); print(t.nlargest(8, 'var_vs_2022T2')[['pct_2022T2', 'pct_2026T1', 'var_vs_2022T2', 'votos_2026']].to_string())

# ---------------------------------------------------------------- seção x perfil
w = sec.pivot_table(index=CHAVE, columns='eleicao', values=['raquel', 'total'], aggfunc='sum')
w.columns = [f'{a}_{b}' for a, b in w.columns]
w = w.reset_index()
info = sec[sec.eleicao == '2026T1'][CHAVE + ['situacao', 'mudou_local', 'transito', 'nm_municipio', 'rd', 'mesorregiao']]
w = w.merge(info, on=CHAVE, how='inner')
w = w[(w.situacao == 'nas_duas') & ~w.transito]
for el in ['2022T1', '2022T2', '2026T1']:
    w[f'pct_{el}'] = w[f'raquel_{el}'] / w[f'total_{el}'] * 100
w['var'] = w.pct_2026T1 - w.pct_2022T2
w = w.merge(perf, on=CHAVE, how='inner')
e = w.eleitores
w['p_superior'] = w.superior / e * 100
w['p_ate_fund_inc'] = w.ate_fund_inc / e * 100
w['p_16_24'] = w.idade_16_24 / e * 100
w['p_60_mais'] = w.idade_60_mais / e * 100
w['p_mulher'] = w.mulher / e * 100
w.to_csv(SAIDA / 'p1_secoes.csv', index=False)
print(f'\n== SEÇÕES comparáveis: {len(w)} (nas duas eleições, sem trânsito); mudou de local: {int(w.mudou_local.sum())}')
print('variação vs 2022 T2 (p.p.):', w['var'].describe().round(2).to_dict())


def corr_pond(x, y, p):
    mx, my = np.average(x, weights=p), np.average(y, weights=p)
    return np.average((x - mx) * (y - my), weights=p) / np.sqrt(np.average((x - mx) ** 2, weights=p) * np.average((y - my) ** 2, weights=p))


VARS = ['p_superior', 'p_ate_fund_inc', 'p_16_24', 'p_60_mais', 'p_mulher']
print('\nCorrelação ponderada pelo total de votos de 2026 (seção):')
print(f"{'variável':16}{'% Raquel 2026':>15}{'% 2022 T2':>12}{'variação':>11}{'var. s/ mudou_local':>21}")
fixo = w[~w.mudou_local]
for v in VARS:
    print(f"{v:16}{corr_pond(w[v], w.pct_2026T1, w.total_2026T1):15.2f}{corr_pond(w[v], w.pct_2022T2, w.total_2026T1):12.2f}"
          f"{corr_pond(w[v], w['var'], w.total_2026T1):11.2f}{corr_pond(fixo[v], fixo['var'], fixo.total_2026T1):21.2f}")

# variação por quintil de escolaridade superior, dentro e fora da RMR
w['q_superior'] = pd.qcut(w.p_superior, 5, labels=['Q1 (menos)', 'Q2', 'Q3', 'Q4', 'Q5 (mais)'])
w['rmr'] = np.where(w.mesorregiao == 'Metropolitana de Recife', 'RMR', 'Interior')


def agrega(df):
    r = df[['raquel_2022T2', 'total_2022T2', 'raquel_2026T1', 'total_2026T1']].sum()
    return pd.Series({'secoes': len(df), 'pct_2022T2': r.raquel_2022T2 / r.total_2022T2 * 100,
                      'pct_2026T1': r.raquel_2026T1 / r.total_2026T1 * 100})


q = w.groupby(['rmr', 'q_superior'], observed=True).apply(agrega, include_groups=False)
q['var'] = q.pct_2026T1 - q.pct_2022T2
faixas = w.groupby('q_superior', observed=True).p_superior.agg(['min', 'max']).round(1)
print('\nFaixas de % com superior (quintis):'); print(faixas.to_string())
print('\nRaquel por quintil de % com superior:'); print(q.round(2).to_string())
q.to_csv(SAIDA / 'p1_quintil_superior.csv')

# renda municipal
m = tabela(['nm_municipio']).reset_index().merge(mun[['nm_municipio', 'renda_pc_mediana', 'rd']], on='nm_municipio')
m['log_renda'] = np.log(m.renda_pc_mediana)
print('\nMunicípio: correlação ponderada (votos 2026) com log da renda mediana per capita (Censo 2022):')
for c in ['pct_2022T2', 'pct_2026T1', 'var_vs_2022T2']:
    print(f'  {c:15}{corr_pond(m.log_renda, m[c], m.votos_2026):.2f}')
m['q_renda'] = pd.qcut(m.renda_pc_mediana, 4, labels=['Q1 (menor)', 'Q2', 'Q3', 'Q4 (maior)'])
print(m.groupby('q_renda', observed=True).apply(
    lambda d: pd.Series({'municipios': len(d), 'renda_mediana_faixa': f'{d.renda_pc_mediana.min():.0f}-{d.renda_pc_mediana.max():.0f}',
                         'var_media_ponderada': np.average(d.var_vs_2022T2, weights=d.votos_2026)}), include_groups=False).to_string())
