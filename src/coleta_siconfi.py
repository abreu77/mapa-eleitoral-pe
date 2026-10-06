"""Coleta e monta as transferências do governo de PE por município (SICONFI, Tesouro Nacional).

- DCA Anexo I-C, 2022 a 2025: receita bruta realizada, com o detalhe por conta.
- RREO Anexo 01, 2026, bimestres 3 (até junho) e 4 (até agosto): só traz o total de
  transferências do estado, corrente e de capital; a de capital serve de aproximação
  do que não é fórmula legal (a corrente inclui a cota do ICMS).

Medidas (contas-mãe, sem dupla contagem):
  convenios = 1.7.2.4 + 2.4.2.2
  amplo     = convenios + (1.7.2.9 - 1.7.2.9.53) + 2.4.2.9
  capital   = 2.4.2 (todas as transferências de capital do estado; comparável com o RREO)
Fora: cota constitucional 1.7.2.1, SUS 1.7.2.3 e 2.4.2.1, royalties 1.7.2.2.

Rodar da raiz do projeto:  python src/coleta_siconfi.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTO = RAIZ.parent / 'dados-siconfi'
BRUTO.mkdir(exist_ok=True)
API = 'https://apidatalake.tesouro.gov.br/ords/siconfi/tt/'
mun = pd.read_csv(RAIZ.parent / 'dados-ibge/municipios_PE_regioes.csv', dtype=str)
mun = mun[mun.nm_municipio != 'Fernando de Noronha']   # distrito estadual, sem prefeitura nem DCA


def baixa(arquivo, url):
    if arquivo.exists():
        return
    for tentativa in range(3):
        try:
            arquivo.write_bytes(urllib.request.urlopen(url, timeout=90).read())
            time.sleep(0.25)
            return
        except Exception:
            time.sleep(3 * (tentativa + 1))
    print('falhou:', url)


def itens(arquivo):
    return json.loads(arquivo.read_text(encoding='utf-8')).get('items', []) if arquivo.exists() else []


for ano in (2022, 2023, 2024, 2025):
    for ib in mun.cd_ibge:
        baixa(BRUTO / f'dca_{ano}_{ib}.json',
              f'{API}dca?an_exercicio={ano}&id_ente={ib}&no_anexo=' + urllib.parse.quote('DCA-Anexo I-C'))
for bim in (3, 4):
    for ib in mun.cd_ibge:
        baixa(BRUTO / f'rreo_2026_b{bim}_{ib}.json',
              f'{API}rreo?an_exercicio=2026&nr_periodo={bim}&co_tipo_demonstrativo=RREO&no_anexo='
              + urllib.parse.quote('RREO-Anexo 01') + f'&id_ente={ib}')

# ---------------------------------------------------------------- DCA
linhas, pop = [], {}
for ano in (2022, 2023, 2024, 2025):
    for ib in mun.cd_ibge:
        for x in itens(BRUTO / f'dca_{ano}_{ib}.json'):
            pop.setdefault(ib, x.get('populacao'))
            if x['coluna'] == 'Receitas Brutas Realizadas':
                linhas.append({'ano': ano, 'cd_ibge': ib, 'cod': x['cod_conta'], 'valor': x['valor']})
d = pd.DataFrame(linhas)
idx = pd.MultiIndex.from_product([mun.cd_ibge, [2022, 2023, 2024, 2025]], names=['cd_ibge', 'ano'])
conta = lambda c: d[d.cod == c].set_index(['cd_ibge', 'ano']).valor.reindex(idx).fillna(0)
t = pd.DataFrame(index=idx)
t['convenios'] = conta('RO1.7.2.4.00.0.0') + conta('RO2.4.2.2.00.0.0')
t['outras'] = conta('RO1.7.2.9.00.0.0') - conta('RO1.7.2.9.53.0.0') + conta('RO2.4.2.9.00.0.0')
t['amplo'] = t.convenios + t.outras
t['capital'] = conta('RO2.4.2.0.00.0.0')
t['constitucional'] = conta('RO1.7.2.1.00.0.0')
t = t.reset_index()

# ---------------------------------------------------------------- RREO 2026 (acumulado até o bimestre)
r = []
for bim in (3, 4):
    for ib in mun.cd_ibge:
        cap = [x['valor'] for x in itens(BRUTO / f'rreo_2026_b{bim}_{ib}.json')
               if x['cod_conta'] == 'TransferenciasDeCapitalDosEstadosEDoDistritoFederalEDeSuasEntidades'
               and x['coluna'].startswith('At') and 'Bimestre (c)' in x['coluna']]
        entregue = bool(itens(BRUTO / f'rreo_2026_b{bim}_{ib}.json'))
        # entregou sem a linha = não recebeu (zero); não entregou = sem dado
        r.append({'ano': f'2026_ate_b{bim}', 'cd_ibge': ib,
                  'capital': (cap[0] if cap else 0.0) if entregue else None, 'entregue': entregue})
r = pd.DataFrame(r)
t = pd.concat([t.assign(ano=t.ano.astype(str)), r.drop(columns='entregue')], ignore_index=True)
t['pop'] = t.cd_ibge.map(pop)
t.to_csv(RAIZ / 'dados_limpos/transferencias_estaduais.csv', index=False)

print('DCA: municípios por ano', d.groupby('ano').cd_ibge.nunique().to_dict())
print('RREO 2026: entregues', r.groupby('ano').entregue.sum().to_dict(),
      '| com transferência de capital do estado > 0', r[r.capital.fillna(0) > 0].groupby('ano').size().to_dict())
print('Capital do estado, R$ milhões:', (t.groupby('ano').capital.sum() / 1e6).round(1).to_dict())
