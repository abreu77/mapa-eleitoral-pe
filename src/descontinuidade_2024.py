"""Descontinuidade em eleições municipais apertadas de 2024 (desenho de Ventura 2021; Feierherd 2020).

Lado do vencedor: lista do Jamildo (aliança declarada em 2026).
Lado do 2º colocado: partido em 2024, mapeado por critério do Diego (06/10/2026):
  bloco Raquel = PSDB, PSD, PP, PODE, UNIÃO; bloco João = PSB, PT, PC do B, PDT, PSOL;
  ambíguos (fora) = MDB, REPUBLICANOS, PL, SOLIDARIEDADE, AVANTE, PRD, PV.
Amostra: vencedor e 2º colocado em blocos opostos. Variável de corte: margem do candidato do
bloco Raquel no turno decisivo (positiva = ele venceu). Desfechos: % de Raquel nos votos totais
em 2026 e, como placebo, em 2022 T2. Regressão linear local, núcleo triangular, inclinações
diferentes de cada lado, erro HC1; janelas de 5, 10 e 15 p.p. e todas as disputas.
Diagnóstico: vencedores cujo partido de 2024 está no bloco oposto ao lado declarado em 2026.
Rodar da raiz do projeto:  python src/descontinuidade_2024.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
L, R = RAIZ / 'dados_limpos', RAIZ / 'resultados'
RAQUEL = {'PSDB', 'PSD', 'PP', 'PODE', 'UNIÃO'}
JOAO = {'PSB', 'PT', 'PC do B', 'PDT', 'PSOL'}
bloco = lambda p: 'Raquel' if p in RAQUEL else 'João' if p in JOAO else None

f = pd.read_csv(L / 'prefeito_2024_finalistas.csv', dtype={'CD_MUNICIPIO': str})
mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_tse': str})
sec = pd.read_csv(L / 'secoes.csv', dtype={'cd_municipio': str})
g = sec.groupby(['cd_municipio', 'eleicao'])[['raquel', 'total']].sum()
pct = (g.raquel / g.total * 100).unstack()

d = f.merge(mun[['cd_tse', 'nm_municipio', 'alianca_prefeito']], left_on='CD_MUNICIPIO', right_on='cd_tse')
d['lado_venc'] = d.alianca_prefeito.map({'Raquel Lyra': 'Raquel', 'João Campos': 'João'})
d['lado_venc_partido2024'] = d.SG_PARTIDO.map(bloco)
d['lado_2o'] = d.SG_PARTIDO_2.map(bloco)
d = d.join(pct[['2022T2', '2026T1']], on='CD_MUNICIPIO')

print('Vencedores: partido de 2024 x lado declarado em 2026 (Jamildo)')
print(pd.crosstab(d.lado_venc_partido2024.fillna('ambíguo'), d.lado_venc).to_string())

s = d[d.lado_2o.notna() & (d.lado_2o != d.lado_venc)].copy()
s['margem_raquel'] = np.where(s.lado_venc == 'Raquel', s.margem, -s.margem)
s['trat'] = (s.margem_raquel > 0).astype(float)
print(f'\nAmostra (lados opostos): {len(s)} municípios; bloco Raquel venceu em {int(s.trat.sum())}')
print('Por janela de margem:', {h: (int(((s.margem_raquel.abs() < h) & (s.trat == 1)).sum()),
                                     int(((s.margem_raquel.abs() < h) & (s.trat == 0)).sum())) for h in (5, 10, 15)},
      '(venceu, perdeu)')


def rd_local(df, y, h):
    x = df.margem_raquel.values
    sel = np.abs(x) < h if h else np.ones(len(x), bool)
    x, yy, t = x[sel], df[y].values[sel], df.trat.values[sel]
    w = np.clip(1 - np.abs(x) / h, 0, None) if h else np.ones(len(x))
    X = np.column_stack([np.ones(len(x)), t, x, t * x])
    sw = np.sqrt(w)
    b, *_ = np.linalg.lstsq(X * sw[:, None], yy * sw, rcond=None)
    e = yy - X @ b
    bread = np.linalg.inv(X.T @ (w[:, None] * X))
    meat = (X * (w * e)[:, None]).T @ (X * (w * e)[:, None])
    n, k = X.shape
    se = np.sqrt(np.diag(bread @ meat @ bread) * n / (n - k))
    q = stats.t.ppf(0.975, n - k)
    return {'janela': h or 'todas', 'n_venceu': int(t.sum()), 'n_perdeu': int((1 - t).sum()),
            'salto_pp': round(b[1], 2), 'IC95': f'{b[1] - q * se[1]:.1f} a {b[1] + q * se[1]:.1f}',
            'p': round(2 * stats.t.sf(abs(b[1] / se[1]), n - k), 3)}


linhas = []
for y, rotulo in [('2026T1', 'Raquel 2026'), ('2022T2', 'placebo: Raquel 2022 T2')]:
    for h in (5, 10, 15, None):
        r = rd_local(s, y, h)
        r['desfecho'] = rotulo
        linhas.append(r)
res = pd.DataFrame(linhas)[['desfecho', 'janela', 'n_venceu', 'n_perdeu', 'salto_pp', 'IC95', 'p']]
res.to_csv(R / 'descontinuidade_2024.csv', index=False)
s.to_csv(R / 'descontinuidade_2024_amostra.csv', index=False)
print('\n' + res.to_string(index=False))
