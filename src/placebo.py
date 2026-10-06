"""Placebo: a aliança de 2026 'prevê' o voto de Raquel em 2022, antes de a aliança existir?

Se prever, parte da associação aliança x voto 2026 é seleção (prefeitos aderiram onde Raquel
já ia bem ou já crescia), não efeito do prefeito. Testes:
  (a) variação de Raquel de 2022 T1 para 2022 T2, com controles do T1 (Raquel, Danilo, Marília), renda, RD
  (b) nível de Raquel em 2022 T2, com renda e RD
  (c) referência: voto de Raquel em 2026 com os mesmos controles de (b)
Ressalva: a lista é de prefeitos que assumiram em 2025; em 2022 parte dos municípios tinha outro prefeito.
Rodar da raiz do projeto:  python src/placebo.py
"""
import contextlib
import io
import runpy
from pathlib import Path

import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(RAIZ / 'src/regressao_municipio.py'))
m, ols, lon = g['m'], g['ols'], g['lon']

mar = lon[lon.eleicao == '2022T1'].groupby('cd_municipio').apply(
    lambda d: d.loc[d.nr_votavel == '77', 'qt_votos'].sum() / d.qt_votos.sum() * 100, include_groups=False)
m['marilia_2022T1'] = m.index.map(mar)
m['var_2022_T1_T2'] = m.raquel_2022T2 - m.raquel_2022T1

TESTES = {
    '(a) variação 2022 T1→T2': ('var_2022_T1_T2', ['aliado_raquel', 'raquel_2022T1', 'danilo_2022T1', 'marilia_2022T1', 'log_renda']),
    '(b) nível 2022 T2': ('raquel_2022T2', ['aliado_raquel', 'log_renda']),
    '(c) referência: nível 2026': ('raquel_2026T1', ['aliado_raquel', 'log_renda']),
}
linhas = []
for nome, (y, xs) in TESTES.items():
    for rd in (False, True):
        for peso in (None, 'votos_2026'):
            t, r2, n = ols(m, y, xs, rd=rd, peso=peso)
            a = t.loc['aliado_raquel']
            q = stats.t.ppf(0.975, n - len(t))
            linhas.append({'teste': nome, 'RD': rd, 'peso': 'votos' if peso else 'nenhum', 'n': n,
                           'coef_aliado_pp': round(a.coef, 2),
                           'IC95': f'{a.coef - q * a.ep_robusto:.2f} a {a.coef + q * a.ep_robusto:.2f}',
                           'p': f'{a.p:.3f}'})
r = pd.DataFrame(linhas)
r.to_csv(RAIZ / 'resultados/placebo.csv', index=False)
print(r.to_string(index=False))
