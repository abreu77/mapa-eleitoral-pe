"""Pergunta 3, parte 1: Bolsa Família por município e voto de Raquel (descritivo).

Fonte: API MI Social do MDS (aplicacoes.mds.gov.br/sagi/servicos/misocial), bruto em
estudos-dados/dados-mds/bf_pe.json. Setembro de 2022 = Auxílio Brasil (pab_qtd_fam_benef_i);
setembro de 2026 = Bolsa Família (qtd_familias_beneficiarias_bolsa_familia_i). Continuidade
conferida na virada: fev/2023 AB 1.728.800 famílias em PE x mar/2023 BF 1.673.337 (−3%).
Cobertura = famílias beneficiárias por 100 habitantes (população do Censo 2022, mesmo campo da API).
O Bolsa Família é programa federal, não do governo do estado.
Modelos: os de regressao_municipio.py (voto de 2022, renda, RD) + cobertura em 2026 e variação
2022→2026, com e sem a aliança. Erro HC1.
Rodar da raiz do projeto:  python src/bolsa_familia.py
"""
import contextlib
import io
import json
import runpy
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
docs = json.loads((RAIZ.parent / 'dados-mds/bf_pe.json').read_text(encoding='utf-8'))['response']['docs']
bf = pd.DataFrame(docs)
bf = bf[bf.anomes_s.isin(['202209', '202609'])]
bf['familias'] = np.where(bf.anomes_s == '202209', bf.pab_qtd_fam_benef_i, bf.qtd_familias_beneficiarias_bolsa_familia_i)
w = bf.pivot_table(index='codigo_ibge', columns='anomes_s', values=['familias', 'populacao_censo_2022_i'], aggfunc='first')
b = pd.DataFrame({'bf_2022': w['familias']['202209'], 'bf_2026': w['familias']['202609'],
                  'pop': w['populacao_censo_2022_i']['202609']})
b['cob_2022'] = b.bf_2022 / b['pop'] * 100
b['cob_2026'] = b.bf_2026 / b['pop'] * 100
b['var_cob'] = b.cob_2026 - b.cob_2022
b['var_pct'] = (b.bf_2026 / b.bf_2022 - 1) * 100
b.index = b.index.astype(str)

with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(RAIZ / 'src/regressao_municipio.py'))
m, ols = g['m'], g['ols']
m['cd6'] = m.cd_ibge.str[:6]                      # API do MDS usa o código IBGE de 6 dígitos
m = m.join(b, on='cd6')
assert m.cob_2026.notna().all(), 'município sem dado do Bolsa Família'
m.reset_index()[['cd_tse', 'nm_municipio', 'alianca_prefeito', 'cob_2022', 'cob_2026', 'var_cob', 'var_pct']].to_csv(
    RAIZ / 'dados_limpos/bolsa_familia_municipio.csv', index=False)

pd.set_option('display.width', 220)
print('Cobertura (famílias por 100 hab.), municípios:')
print(m[['cob_2022', 'cob_2026', 'var_cob', 'var_pct']].describe().round(2).to_string())
print('\nMediana por aliança do prefeito:')
print(m.groupby('alianca_prefeito')[['cob_2022', 'cob_2026', 'var_cob', 'var_pct']].median().round(2).to_string())
print('\nCorrelação simples (municípios):',
      {c: round(np.corrcoef(m[c], m.raquel_2026T1)[0, 1], 2) for c in ['cob_2022', 'cob_2026', 'var_cob']},
      '| com log da renda:', round(np.corrcoef(m.cob_2026, m.log_renda)[0, 1], 2))

BASE = ['raquel_2022T1', 'raquel_2022T2', 'danilo_2022T1', 'log_renda']
linhas = []
for var in ['cob_2026', 'var_cob']:
    x = m[var]
    iqr = np.percentile(x, 75) - np.percentile(x, 25)
    for com in (False, True):
        xs = BASE + [var] + (['aliado_raquel'] if com else [])
        for rd in (False, True):
            for peso in (None, 'votos_2026'):
                t, r2, n = ols(m, 'raquel_2026T1', xs, rd=rd, peso=peso)
                bb, se = t.loc[var, 'coef'], t.loc[var, 'ep_robusto']
                q = stats.t.ppf(0.975, n - len(t))
                linhas.append({'variavel': var, 'com_alianca': com, 'RD': rd, 'peso': 'votos' if peso else 'nenhum',
                               'p25_p75_pp': round(bb * iqr, 2),
                               'IC95': f'{(bb - q * se) * iqr:.2f} a {(bb + q * se) * iqr:.2f}',
                               'p': round(t.loc[var, 'p'], 3),
                               'coef_alianca': round(t.loc['aliado_raquel', 'coef'], 2) if com else None})
r = pd.DataFrame(linhas)
r.to_csv(RAIZ / 'resultados/bolsa_familia_regressao.csv', index=False)
print('\nVoto de Raquel 2026: diferença entre município no p25 e no p75 da variável (p.p.)')
print(r.to_string(index=False))
