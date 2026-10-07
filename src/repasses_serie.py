"""Repasses do governo de PE aos municípios, 2024 a 2026, pela aliança dos prefeitos atuais.

Aliança: lado declarado em 2026 pelos prefeitos que tomaram posse em 2025 (lista do Jamildo.com).
Em 2024 o prefeito era outro em parte dos municípios (eleito em 2020): a série usa a aliança atual
mesmo assim, por escolha do Diego, e 2024 fica com essa ressalva.

Duas comparações:
1. Ano inteiro (DCA, 2024 e 2025): medida ampla (convênios + outras transferências do estado) e
   capital do estado (2.4.2).
2. Mesmo período e mesma medida (RREO, capital do estado, acumulado até junho e até agosto) em
   2024, 2025 e 2026. Só municípios que entregaram o RREO nos três anos do período (painel fechado).
   Junho importa: a Lei 9.504/97, art. 73, VI, "a", proíbe transferência voluntária nos três meses
   antes da eleição (2024: municipal; 2026: estadual).

Por grupo: cobertura (% que recebeu algo), mediana em R$ por habitante, razão das medianas
(aliado/oposição) e teste de Mann-Whitney; parcela do dinheiro x parcela da população.
Variação 2025 -> 2026 no mesmo município e período: mediana da diferença por grupo e Mann-Whitney.

Rodar da raiz do projeto:  python src/repasses_serie.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

RAIZ = Path(__file__).resolve().parents[1]
L, SAIDA = RAIZ / 'dados_limpos', RAIZ / 'resultados'

mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_ibge': str})
mun = mun[mun.alianca_prefeito != 'sem prefeito'].set_index('cd_ibge')
aliado = mun.alianca_prefeito.eq('Raquel Lyra')
tr = pd.read_csv(L / 'transferencias_estaduais.csv', dtype={'cd_ibge': str, 'ano': str})
pop = tr.groupby('cd_ibge').pop.first()


def compara(valor, nome):
    """valor: R$ por município (índice cd_ibge), já sem os que não têm dado."""
    v = valor.dropna()
    pc = v / pop.reindex(v.index)
    a, o = pc[aliado.reindex(v.index)], pc[~aliado.reindex(v.index)]
    p = mannwhitneyu(a, o).pvalue
    din = v[aliado.reindex(v.index)].sum() / v.sum() * 100 if v.sum() else np.nan
    popa = pop.reindex(a.index).sum() / pop.reindex(v.index).sum() * 100
    return {'medida': nome, 'municipios': len(v), 'aliado_n': len(a), 'oposicao_n': len(o),
            'cobertura_aliado_%': (a > 0).mean() * 100, 'cobertura_oposicao_%': (o > 0).mean() * 100,
            'mediana_aliado': a.median(), 'mediana_oposicao': o.median(),
            'razao_medianas': a.median() / o.median() if o.median() else np.nan, 'p_mann_whitney': p,
            'aliado_%_populacao': popa, 'aliado_%_dinheiro': din}


pv = tr.pivot_table(index='cd_ibge', columns='ano', values=['amplo', 'capital'], aggfunc='first').reindex(mun.index)
linhas = []
# 1. ano inteiro (DCA)
for ano in ('2024', '2025'):
    linhas.append(compara(pv['amplo'][ano], f'{ano} ano inteiro · amplo (DCA)'))
    linhas.append(compara(pv['capital'][ano], f'{ano} ano inteiro · capital do estado (DCA)'))
# conferência com o registrado antes (2026 até junho, todos os que entregaram)
linhas.append(compara(pv['capital']['2026_ate_b3'], '2026 até junho · capital (RREO, todos que entregaram)'))

# 2. mesmo período, painel fechado
variacao = []
for bim, periodo in ((3, 'junho'), (4, 'agosto')):
    cols = [f'{a}_ate_b{bim}' for a in (2024, 2025, 2026)]
    painel = pv['capital'][cols].dropna()
    for c in cols:
        linhas.append(compara(painel[c], f'{c[:4]} até {periodo} · capital (RREO, painel de {len(painel)})'))
    # variação 2025 -> 2026 no mesmo município, R$ por habitante
    d = (painel[cols[2]] - painel[cols[1]]) / pop.reindex(painel.index)
    da, do = d[aliado.reindex(d.index)], d[~aliado.reindex(d.index)]
    variacao.append({'periodo': f'até {periodo}', 'municipios': len(d),
                     'mediana_variacao_aliado': da.median(), 'mediana_variacao_oposicao': do.median(),
                     'subiu_aliado_%': (da > 0).mean() * 100, 'subiu_oposicao_%': (do > 0).mean() * 100,
                     'p_mann_whitney': mannwhitneyu(da, do).pvalue})

res = pd.DataFrame(linhas)
var = pd.DataFrame(variacao)
res.round(3).to_csv(SAIDA / 'repasses_serie.csv', index=False)
var.round(3).to_csv(SAIDA / 'repasses_variacao_2025_2026.csv', index=False)
pd.set_option('display.width', 250)
print('R$ por habitante; aliado = prefeito com Raquel; oposição = prefeito com João')
print(res[['medida', 'municipios', 'cobertura_aliado_%', 'cobertura_oposicao_%', 'mediana_aliado', 'mediana_oposicao',
           'razao_medianas', 'p_mann_whitney', 'aliado_%_populacao', 'aliado_%_dinheiro']].round(3).to_string(index=False))
print('\nVariação 2025 -> 2026 no mesmo município e período (R$ por habitante, capital do estado, RREO)')
print(var.round(3).to_string(index=False))
