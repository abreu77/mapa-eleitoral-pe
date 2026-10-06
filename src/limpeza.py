"""Limpeza: governador PE, 2022 (1º e 2º turnos) e 2026 (1º turno).

Lê os arquivos brutos do TSE e do IBGE em estudos-dados/dados-*/ e grava as
tabelas limpas em dados_limpos/. Decisões resumidas no README (seção "Método").

Rodar da raiz do projeto:  python src/limpeza.py
"""
import difflib
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ.parent
TSE = DADOS / 'dados-tse'
IBGE = DADOS / 'dados-ibge'
SAIDA = RAIZ / 'dados_limpos'
SAIDA.mkdir(exist_ok=True)

ELEICOES = {  # chave -> (arquivo de votos, turno, arquivo de locais)
    '2022T1': (TSE / '2022/votacao_secao_2022_PE/votacao_secao_2022_PE.csv', '1',
               TSE / '2022/eleitorado_local_votacao_2022/eleitorado_local_votacao_2022_PE.csv'),
    '2022T2': (TSE / '2022/votacao_secao_2022_PE/votacao_secao_2022_PE.csv', '2',
               TSE / '2022/eleitorado_local_votacao_2022/eleitorado_local_votacao_2022_PE.csv'),
    '2026T1': (TSE / '2026/votacao_secao_2026_PE/votacao_secao_2026_PE.csv', '1',
               TSE / '2026/eleitorado_local_votacao_2026/eleitorado_local_votacao_2026_PE.csv'),
}
RAQUEL = '45'                     # 2022: PSDB 45; 2026: PSD 55 (ver nr_raquel)
NR_RAQUEL = {'2022T1': '45', '2022T2': '45', '2026T1': '55'}
BLOCO_PSB = {'2022T1': '40', '2022T2': None, '2026T1': '40'}   # T2 2022 fora da aba
BRANCO, NULO = '95', '96'
CHAVE = ['nr_zona', 'nr_secao']


def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', s)).strip()


def ler_tse(caminho, **kw):
    return pd.read_csv(caminho, sep=';', encoding='latin1', dtype=str, **kw)


def coord(x):
    v = pd.to_numeric(x.str.replace(',', '.', regex=False), errors='coerce')
    return v.where(v != -1)


# ---------------------------------------------------------------- votos
def votos_governador(caminho, turno):
    """Votos de governador por seção, de um turno. Lê em blocos (arquivo de ~800 MB)."""
    cols = ['NR_TURNO', 'DS_CARGO', 'CD_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'NR_LOCAL_VOTACAO',
            'NR_VOTAVEL', 'NM_VOTAVEL', 'QT_VOTOS']
    partes = [c[(c.DS_CARGO.str.upper() == 'GOVERNADOR') & (c.NR_TURNO == turno)]
              for c in ler_tse(caminho, usecols=cols, chunksize=1_000_000)]
    v = pd.concat(partes)
    v.columns = [c.lower() for c in v.columns]
    v['qt_votos'] = v.qt_votos.astype(int)
    return v.drop(columns=['nr_turno', 'ds_cargo'])


longo = []
for el, (arq, turno, _) in ELEICOES.items():
    v = votos_governador(arq, turno)
    v.insert(0, 'eleicao', el)
    longo.append(v)
longo = pd.concat(longo, ignore_index=True)
longo.to_csv(SAIDA / 'votos_secao_longo.csv', index=False)


def resumo_secao(v, el):
    """Uma linha por seção: totais, Raquel, bloco PSB, vencedor."""
    g = v.groupby(CHAVE + ['cd_municipio', 'nr_local_votacao'])
    out = g.qt_votos.sum().rename('total').to_frame()
    por = v.pivot_table(index=CHAVE, columns='nr_votavel', values='qt_votos', aggfunc='sum', fill_value=0)
    out = out.reset_index().merge(por, left_on=CHAVE, right_index=True)
    out['brancos'] = out.get(BRANCO, 0)
    out['nulos'] = out.get(NULO, 0)
    out['validos'] = out.total - out.brancos - out.nulos
    out['raquel'] = out[NR_RAQUEL[el]]
    out['bloco_psb'] = out[BLOCO_PSB[el]] if BLOCO_PSB[el] else pd.NA
    cand = [c for c in por.columns if c not in (BRANCO, NULO)]
    out['vencedor'] = out[cand].idxmax(axis=1)
    out['empate'] = out[cand].eq(out[cand].max(axis=1), axis=0).sum(axis=1) > 1
    out['vencedor'] = out.vencedor.where(~out.empate, 'empate')
    out.insert(0, 'eleicao', el)
    return out[['eleicao'] + CHAVE + ['cd_municipio', 'nr_local_votacao', 'total', 'validos', 'brancos',
                                      'nulos', 'raquel', 'bloco_psb', 'vencedor', 'empate']]


secoes = pd.concat([resumo_secao(longo[longo.eleicao == el], el) for el in ELEICOES], ignore_index=True)

# comparecimento (detalhe de votação por seção): aptos e abstenções de governador
DETALHE = {'2022': TSE / '2022/detalhe_votacao_secao_2022/detalhe_votacao_secao_2022_PE.csv',
           '2026': TSE / '2026/detalhe_votacao_secao_2026/detalhe_votacao_secao_2026_PE.csv'}
det = []
for ano, arq in DETALHE.items():
    d = ler_tse(arq, usecols=['NR_TURNO', 'DS_CARGO', 'NR_ZONA', 'NR_SECAO', 'QT_APTOS', 'QT_ABSTENCOES', 'QT_COMPARECIMENTO'])
    d = d[d.DS_CARGO.str.upper() == 'GOVERNADOR']
    d['eleicao'] = ano + 'T' + d.NR_TURNO
    det.append(d)
det = pd.concat(det).rename(columns=str.lower).drop(columns=['nr_turno', 'ds_cargo'])
for c in ('qt_aptos', 'qt_abstencoes', 'qt_comparecimento'):
    det[c] = det[c].astype(int)
secoes = secoes.merge(det.rename(columns={'qt_aptos': 'aptos', 'qt_abstencoes': 'abstencoes'}),
                      on=['eleicao'] + CHAVE, how='left')
assert (secoes.qt_comparecimento == secoes.total).all(), 'comparecimento difere do total de votos'
secoes = secoes.drop(columns='qt_comparecimento')
nomes = longo.drop_duplicates(['eleicao', 'nr_votavel'])[['eleicao', 'nr_votavel', 'nm_votavel']]
nomes.to_csv(SAIDA / 'candidatos.csv', index=False)

# ---------------------------------------------------------------- locais e coordenadas
def locais(caminho, turno):
    l = ler_tse(caminho)
    l = l[(l.NR_TURNO == turno) & (l.DS_TIPO_SECAO_AGREGADA == 'Principal')]
    l = l.rename(columns=str.lower)
    l['lat'], l['lon'] = coord(l.nr_latitude), coord(l.nr_longitude)
    return l[CHAVE + ['cd_municipio', 'nr_local_votacao', 'nm_local_votacao', 'ds_endereco', 'nm_bairro',
                      'lat', 'lon', 'qt_eleitor_secao']]


loc = {el: locais(ELEICOES[el][2], ELEICOES[el][1]) for el in ELEICOES}

# 2022 sem coordenada: recupera pelo cadastro de 2026
ref = loc['2026T1'].dropna(subset=['lat']).drop_duplicates(['nr_zona', 'nr_local_votacao'])
ref = ref.assign(kn=ref.cd_municipio + '|' + ref.nm_local_votacao.map(norm),
                 kz=ref.nr_zona + '|' + ref.nr_local_votacao)
por_nome = ref.drop_duplicates('kn').set_index('kn')[['lat', 'lon']]
por_num = ref.set_index('kz')[['lat', 'lon', 'nm_local_votacao']]
for el in ('2022T1', '2022T2'):
    l = loc[el]
    l['coord_origem'] = l.lat.notna().map({True: 'proprio', False: None})
    falta = l.lat.isna()
    kn = l.cd_municipio + '|' + l.nm_local_votacao.map(norm)
    kz = l.nr_zona + '|' + l.nr_local_votacao
    achou = falta & kn.isin(por_nome.index)
    l.loc[achou, ['lat', 'lon']] = por_nome.loc[kn[achou]].values
    l.loc[achou, 'coord_origem'] = 'cadastro_2026_nome'
    falta = l.lat.isna()
    cand = falta & kz.isin(por_num.index)
    parecido = [difflib.SequenceMatcher(None, norm(a), norm(por_num.loc[k, 'nm_local_votacao'])).ratio() >= 0.6
                for a, k in zip(l.loc[cand, 'nm_local_votacao'], kz[cand])]
    idx = l.index[cand][parecido]
    l.loc[idx, ['lat', 'lon']] = por_num.loc[kz[idx], ['lat', 'lon']].values
    l.loc[idx, 'coord_origem'] = 'cadastro_2026_numero'
    l['coord_origem'] = l.coord_origem.fillna('sem_coordenada')
loc['2026T1']['coord_origem'] = loc['2026T1'].lat.notna().map({True: 'proprio', False: 'sem_coordenada'})

# coordenadas fora de PE (inclui Noronha: lon até -32) viram sem_coordenada
for l in loc.values():
    fora = l.lat.notna() & ~(l.lat.between(-10, -3) & l.lon.between(-42, -32))
    l.loc[fora, ['lat', 'lon']] = pd.NA
    l.loc[fora, 'coord_origem'] = 'fora_de_PE'

secoes = pd.concat([
    s.merge(loc[el].drop(columns=['cd_municipio', 'nr_local_votacao']), on=CHAVE, how='left')
    for el, s in secoes.groupby('eleicao')], ignore_index=True)

# ---------------------------------------------------------------- casamento 2022 x 2026
a = loc['2022T1'][CHAVE + ['nr_local_votacao', 'nm_local_votacao']]
b = loc['2026T1'][CHAVE + ['nr_local_votacao', 'nm_local_votacao']]
cas = a.merge(b, on=CHAVE, how='outer', suffixes=('_2022', '_2026'), indicator=True)
cas['situacao'] = cas._merge.map({'both': 'nas_duas', 'left_only': 'so_2022', 'right_only': 'so_2026'})
mesmo_num = cas.nr_local_votacao_2022 == cas.nr_local_votacao_2026
mesmo_nome = cas.nm_local_votacao_2022.map(norm) == cas.nm_local_votacao_2026.map(norm)
cas['mudou_local'] = (cas.situacao == 'nas_duas') & ~mesmo_num & ~mesmo_nome
cas = cas.drop(columns='_merge')
cas.to_csv(SAIDA / 'casamento_secoes.csv', index=False)
secoes = secoes.merge(cas[CHAVE + ['situacao', 'mudou_local']], on=CHAVE, how='left')
# seção de voto em trânsito: sem eleitor cadastrado, recebe eleitor de fora; não representa o bairro
secoes['transito'] = (pd.to_numeric(secoes.qt_eleitor_secao, errors='coerce') == 0) | \
    secoes.nm_local_votacao.fillna('').str.upper().str.contains('TRÂNSITO|TRANSITO')
secoes.to_csv(SAIDA / 'secoes.csv', index=False)

# ---------------------------------------------------------------- municípios
mun = pd.read_csv(IBGE / 'municipios_PE_regioes.csv', dtype=str)
renda = pd.read_csv(IBGE / 'censo2022/renda_pc_censo2022_PE.csv', dtype=str)
renda = renda[renda.nivel == 'N6'][['cd_ibge', 'renda_pc_media', 'renda_pc_mediana']]
mun = mun.merge(renda, on='cd_ibge', how='left')

FIX_JAMILDO = {'barra da guabiraba': 'barra de guabiraba', 'sao caetano': 'sao caitano'}
jam = pd.read_csv(RAIZ / 'coleta/jamildo_apoios_20261006.csv', dtype=str)
jam.columns = ['id', 'cidade', 'prefeito', 'partido_antigo', 'partido_prefeito', 'foto', 'alianca_prefeito',
               'pop', 'nome_completo', 'regiao_jamildo']
jam['k'] = jam.cidade.map(norm).replace(FIX_JAMILDO)
mun['k'] = mun.nm_municipio.map(norm)
mun = mun.merge(jam[['k', 'prefeito', 'partido_prefeito', 'alianca_prefeito']], on='k', how='left').drop(columns='k')
mun['alianca_prefeito'] = mun.alianca_prefeito.fillna('sem prefeito')
mun.to_csv(SAIDA / 'municipios.csv', index=False)

# ---------------------------------------------------------------- perfil do eleitorado 2026
ESC = {'ANALFABETO': 'ate_fund_inc', 'LÊ E ESCREVE': 'ate_fund_inc', 'ENSINO FUNDAMENTAL INCOMPLETO': 'ate_fund_inc',
       'ENSINO FUNDAMENTAL COMPLETO': 'fund_medio', 'ENSINO MÉDIO INCOMPLETO': 'fund_medio',
       'ENSINO MÉDIO COMPLETO': 'medio_completo', 'SUPERIOR INCOMPLETO': 'superior', 'SUPERIOR COMPLETO': 'superior'}


def faixa(ds):
    n = int(re.match(r'\d+', ds).group()) if re.match(r'\d+', ds) else None
    if n is None:
        return 'idade_ni'
    return 'idade_16_24' if n < 25 else 'idade_25_44' if n < 45 else 'idade_45_59' if n < 60 else 'idade_60_mais'


p = ler_tse(TSE / '2026/perfil_eleitor_secao_2026_PE/perfil_eleitor_secao_2026_PE.csv',
            usecols=['NR_ZONA', 'NR_SECAO', 'DS_GENERO', 'DS_FAIXA_ETARIA', 'DS_GRAU_ESCOLARIDADE', 'QT_ELEITORES'])
p.columns = [c.lower() for c in p.columns]
p['q'] = p.qt_eleitores.astype(int)
# seção agregada -> principal
mapa = ler_tse(ELEICOES['2026T1'][2], usecols=['NR_ZONA', 'NR_SECAO', 'NR_SECAO_PRINCIPAL'])
mapa.columns = ['nr_zona', 'nr_secao', 'nr_secao_principal']
p = p.merge(mapa, on=CHAVE, how='left')
tem_principal = p.nr_secao_principal.notna() & (p.nr_secao_principal != '-1')   # principal vem com "-1"
p['nr_secao'] = p.nr_secao_principal.where(tem_principal, p.nr_secao)
p['esc'] = p.ds_grau_escolaridade.map(ESC).fillna('esc_ni')
p['idade'] = p.ds_faixa_etaria.map(faixa)
p['mulher'] = (p.ds_genero == 'FEMININO').astype(int) * p.q
perf = pd.concat([
    p.groupby(CHAVE).q.sum().rename('eleitores'),
    p.groupby(CHAVE).mulher.sum(),
    p.pivot_table(index=CHAVE, columns='esc', values='q', aggfunc='sum', fill_value=0),
    p.pivot_table(index=CHAVE, columns='idade', values='q', aggfunc='sum', fill_value=0),
], axis=1).reset_index()
perf.to_csv(SAIDA / 'perfil_secao_2026.csv', index=False)

# ---------------------------------------------------------------- conferências
ofic = {'2022T1': None, '2022T2': None, '2026T1': 5_266_852}   # válidos 2026 pelo arquivo munzona
print('Seções por eleição:', secoes.groupby('eleicao').size().to_dict())
print('Válidos:', secoes.groupby('eleicao').validos.sum().to_dict(), '| 2026 esperado', ofic['2026T1'])
print('Aptos:', secoes.groupby('eleicao').aptos.sum().to_dict(), '| comparecimento %:',
      (secoes.groupby('eleicao').total.sum() / secoes.groupby('eleicao').aptos.sum() * 100).round(2).to_dict())
print('Raquel % do total:', (secoes.groupby('eleicao').raquel.sum() / secoes.groupby('eleicao').total.sum() * 100).round(2).to_dict())
print('Origem da coordenada:', secoes.groupby(['eleicao', 'coord_origem']).size().to_dict())
print('Casamento:', cas.situacao.value_counts().to_dict(), '| mudou_local', int(cas.mudou_local.sum()))
print('Empates de vencedor:', secoes.groupby('eleicao').empate.sum().to_dict())
print('Municípios:', len(mun), mun.alianca_prefeito.value_counts().to_dict(), '| sem renda', mun.renda_pc_media.isna().sum())
print('Perfil: seções', len(perf), 'eleitores', perf.eleitores.sum())
