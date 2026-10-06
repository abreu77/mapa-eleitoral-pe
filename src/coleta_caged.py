"""Pergunta 3, parte 2: saldo de emprego formal por município (Novo CAGED), out/2025 a ago/2026.

Fonte: microdados do Novo CAGED, FTP do PDET/MTE (ftp.mtps.gov.br/pdet/microdados/NOVO CAGED),
arquivos nacionais mensais em .7z. Saldo = movimentações do mês (MOV) + declaradas fora do prazo
(FOR) − exclusões (EXC), como no método de divulgação do Novo CAGED. Só PE (uf = 26).
Brutos em estudos-dados/dados-caged/; resultado em dados_limpos/caged_municipio.csv.
Rodar da raiz do projeto:  python src/coleta_caged.py
"""
import io
import time
import urllib.request
from pathlib import Path

import pandas as pd
import py7zr

RAIZ = Path(__file__).resolve().parents[1]
BRUTO = RAIZ.parent / 'dados-caged'
BRUTO.mkdir(exist_ok=True)
FTP = 'ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED/'
MESES = [f'{a}{m:02d}' for a, m in [(2025, 10), (2025, 11), (2025, 12)] + [(2026, k) for k in range(1, 9)]]
SINAL = {'MOV': 1, 'FOR': 1, 'EXC': -1}


def baixa(comp, tipo):
    f = BRUTO / f'CAGED{tipo}{comp}.7z'
    if not f.exists():
        url = f'{FTP}{comp[:4]}/{comp}/CAGED{tipo}{comp}.7z'
        for tentativa in range(3):
            try:
                f.write_bytes(urllib.request.urlopen(url, timeout=600).read())
                break
            except Exception as e:
                print('tentativa', tentativa + 1, 'falhou:', url, e)
                time.sleep(10)
    return f


def saldo_pe(arquivo):
    tmp = BRUTO / 'tmp'
    tmp.mkdir(exist_ok=True)
    with py7zr.SevenZipFile(arquivo, 'r') as z:
        z.extractall(path=tmp)
    (txt,) = list(tmp.iterdir())
    partes = []
    for bloco in pd.read_csv(txt, sep=';', dtype=str, chunksize=500_000, encoding='utf-8'):
        bloco.columns = [c.lower().replace('ç', 'c').replace('ã', 'a') for c in bloco.columns]
        pe = bloco[bloco.uf == '26']
        partes.append(pe.groupby('município' if 'município' in pe.columns else 'municipio')
                      ['saldomovimentacao' if 'saldomovimentacao' in pe.columns else 'saldomovimentação']
                      .apply(lambda s: s.astype(int).sum()))
    txt.unlink()   # o texto extraído é grande; fica só o .7z
    return pd.concat(partes).groupby(level=0).sum()


linhas = []
for comp in MESES:
    for tipo, sinal in SINAL.items():
        f = baixa(comp, tipo)
        s = saldo_pe(f) * sinal
        linhas.append(s.rename('saldo').reset_index().assign(competencia=comp, tipo=tipo))
        print(comp, tipo, 'municípios', len(s), 'saldo PE', int(s.sum()), flush=True)
d = pd.concat(linhas)
d.columns = ['cd_ibge6', 'saldo', 'competencia', 'tipo']
d.to_csv(BRUTO / 'caged_pe_out2025_ago2026_detalhe.csv', index=False)
tot = d.groupby('cd_ibge6').saldo.sum().rename('saldo_out25_ago26').reset_index()
tot.to_csv(RAIZ / 'dados_limpos/caged_municipio.csv', index=False)
print('Saldo PE no período:', int(tot.saldo_out25_ago26.sum()), '| municípios com registro:', len(tot))
