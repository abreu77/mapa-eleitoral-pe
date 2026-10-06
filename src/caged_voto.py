"""Pergunta 3, parte 2: saldo de emprego formal (Novo CAGED, out/2025–ago/2026) e voto de Raquel.

Saldo por mil habitantes (população do Censo 2022, campo da API do MDS). Mesmos modelos de
bolsa_familia.py: voto de 2022, renda, RD, com e sem a aliança; erro HC1; efeito entre
município no p25 e no p75 do saldo. Descritivo. CAGED cobre só emprego com carteira.
Rodar da raiz do projeto:  python src/caged_voto.py   (depois de src/coleta_caged.py)
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
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(RAIZ / 'src/regressao_municipio.py'))
m, ols = g['m'], g['ols']

docs = json.loads((RAIZ.parent / 'dados-mds/bf_pe.json').read_text(encoding='utf-8'))['response']['docs']
pop = pd.DataFrame(docs).drop_duplicates('codigo_ibge').set_index('codigo_ibge').populacao_censo_2022_i
cg = pd.read_csv(RAIZ / 'dados_limpos/caged_municipio.csv', dtype={'cd_ibge6': str}).set_index('cd_ibge6')
m['cd6'] = m.cd_ibge.str[:6]
m['saldo'] = m.cd6.map(cg.saldo_out25_ago26).fillna(0)
m['saldo_mil_hab'] = m.saldo / m.cd6.map(pop) * 1000
assert m.saldo_mil_hab.notna().all()
m.reset_index()[['cd_tse', 'nm_municipio', 'alianca_prefeito', 'saldo', 'saldo_mil_hab']].to_csv(
    RAIZ / 'dados_limpos/caged_municipio_voto.csv', index=False)

pd.set_option('display.width', 220)
print('Saldo PE out/2025–ago/2026:', int(m.saldo.sum()))
print('Saldo por mil hab., municípios:'); print(m.saldo_mil_hab.describe().round(2).to_string())
print('Mediana por aliança:', m.groupby('alianca_prefeito').saldo_mil_hab.median().round(2).to_dict())
print('Correlação simples com Raquel 2026:', round(np.corrcoef(m.saldo_mil_hab, m.raquel_2026T1)[0, 1], 2))

BASE = ['raquel_2022T1', 'raquel_2022T2', 'danilo_2022T1', 'log_renda']
iqr = np.percentile(m.saldo_mil_hab, 75) - np.percentile(m.saldo_mil_hab, 25)
linhas = []
for com in (False, True):
    xs = BASE + ['saldo_mil_hab'] + (['aliado_raquel'] if com else [])
    for rd in (False, True):
        for peso in (None, 'votos_2026'):
            t, r2, n = ols(m, 'raquel_2026T1', xs, rd=rd, peso=peso)
            b, se = t.loc['saldo_mil_hab', 'coef'], t.loc['saldo_mil_hab', 'ep_robusto']
            q = stats.t.ppf(0.975, n - len(t))
            linhas.append({'com_alianca': com, 'RD': rd, 'peso': 'votos' if peso else 'nenhum',
                           'p25_p75_pp': round(b * iqr, 2), 'IC95': f'{(b - q * se) * iqr:.2f} a {(b + q * se) * iqr:.2f}',
                           'p': round(t.loc['saldo_mil_hab', 'p'], 3),
                           'coef_alianca': round(t.loc['aliado_raquel', 'coef'], 2) if com else None})
r = pd.DataFrame(linhas)
r.to_csv(RAIZ / 'resultados/caged_regressao.csv', index=False)
print(f'\nVoto de Raquel 2026: município no p25 x p75 do saldo por mil hab. (IQR = {iqr:.1f})')
print(r.to_string(index=False))
