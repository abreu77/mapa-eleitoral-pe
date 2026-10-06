"""Deputados estaduais e federais de 2026 por bloco: Raquel x João.

Lado de cada voto: o partido (dois primeiros dígitos do número) segue a coligação de
governador de 2026 no TSE (consulta_coligacao_2026). Fora das duas coligações = "outros".
Ajuste individual: candidato com apoio público ao outro lado muda de bloco (só os votos
nominais dele; o voto de legenda fica com o partido). Cada ajuste tem fonte em AJUSTES.
Base dos percentuais: votos válidos de deputado (nominais + legenda).

Saídas em dados_limpos/: deputados_secao.csv (votos por seção, cargo e bloco),
deputados_candidato_secao.csv (votos nominais por candidato e seção) e
deputados_candidatos.csv (candidatos, bloco, situação, votos).
Rodar da raiz do projeto:  python src/deputados.py
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DADOS = next(p for p in RAIZ.parents if (p / 'dados-tse').is_dir())   # estudos-dados/ (vale também numa worktree)
TSE = DADOS / 'dados-tse/2026'
SAIDA = RAIZ / 'dados_limpos'
CARGOS = {'DEPUTADO FEDERAL': 'federal', 'DEPUTADO ESTADUAL': 'estadual'}
BRANCO, NULO = '95', '96'
COLIGACAO = {'PERNAMBUCO DE CORAÇÃO': 'R', 'FRENTE POPULAR DE PERNAMBUCO': 'J'}

# número do candidato -> (bloco, fonte). Só eleitos, só com apoio público conferido (06/10/2026).
# Estaduais: lista do Jamildo.com com o lado de cada um dos 49 eleitos.
# Federais: sem lista pronta; notícia por deputado. Sem fonte achada, fica o bloco da coligação.
JAMILDO_ALEPE = ('Jamildo.com, 05/10/2026: https://jamildo.com/politica/'
                 'mesmo-com-psd-e-psb-empatados-maioria-da-alepe-sera-aliada-de-raquel-lyra.html')
AJUSTES = {
    '22222': ('R', JAMILDO_ALEPE),                                  # André Ferreira (PL)
    '13113': ('R', JAMILDO_ALEPE + ' (dissidente do PT)'),          # João Paulo (PT)
    '43643': ('R', JAMILDO_ALEPE),                                  # João de Nadegi (PV)
    '43555': ('R', JAMILDO_ALEPE),                                  # Joaquim Lira (PV)
    '43456': ('R', JAMILDO_ALEPE + ' ("pode seguir" o grupo, que apoiou Raquel; decisão do Diego)'),  # Lara Santana (PV)
    '30630': ('R', JAMILDO_ALEPE),                                  # Renato Antunes (NOVO)
    '20111': ('J', JAMILDO_ALEPE + ' (dissidente no Podemos)'),     # Fabrizio Ferraz (PODE)
    '11111': ('O', JAMILDO_ALEPE + ' (sem declaração de apoio)'),   # Gleide Ângelo (PP)
    '4333': ('R', 'Folha de Pernambuco: https://www.folhape.com.br/colunistas/blogdafolha/'
                  'clodoaldo-magalhaes-defende-apoio-do-pv-a-raquel-lyra-apesar-de-o-partido-ser-minoria-na-federacao/56704/'),
    '3030': ('R', 'NOVO declarou apoio a Raquel (Diario de Pernambuco, 10/07/2026: https://www.diariodepernambuco.com.br/'
                  'politica/2026/07/11718539-partido-novo-em-pernambuco-declara-apoio-a-reeleicao-de-raquel-lyra.html); '
                  'eleito do partido, decisão do Diego'),           # Eduardo Moura (NOVO)
}


def ler(caminho, **kw):
    return pd.read_csv(caminho, sep=';', encoding='latin1', dtype=str, **kw)


# ---------------------------------------------------------------- partido -> bloco (coligação de governador)
co = ler(TSE / 'consulta_coligacao_2026/consulta_coligacao_2026_PE.csv')
co = co[co.DS_CARGO.str.upper() == 'GOVERNADOR']
partido_bloco = {}
for r in co.itertuples():
    bloco = COLIGACAO.get(r.NM_COLIGACAO, 'O')
    # a composição traz as federações por extenso: "45-PSDB / 23-CIDADANIA"
    numeros = {r.NR_PARTIDO} | set(pd.Series(r.DS_COMPOSICAO_COLIGACAO).str.findall(r'(\d{2})-').iat[0])
    for n in numeros:
        partido_bloco.setdefault(n, bloco)
cand = ler(TSE / 'consulta_cand_2026/consulta_cand_2026_PE.csv')
cand = cand[cand.DS_CARGO.str.upper().isin(CARGOS)]
sigla = cand.drop_duplicates('NR_PARTIDO').set_index('NR_PARTIDO').SG_PARTIDO
faltam = {n: sigla.get(n) for n in sorted(set(cand.NR_PARTIDO) - set(partido_bloco))}
print('partidos sem coligação de governador (ficam em "outros"):', faltam)
print('bloco Raquel:', sorted(sigla.get(n, n) for n, b in partido_bloco.items() if b == 'R'))
print('bloco João:', sorted(sigla.get(n, n) for n, b in partido_bloco.items() if b == 'J'))

# ---------------------------------------------------------------- votos por seção
cols = ['NR_TURNO', 'DS_CARGO', 'CD_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'NR_LOCAL_VOTACAO', 'NR_VOTAVEL', 'QT_VOTOS']
partes = [c[c.DS_CARGO.str.upper().isin(CARGOS)]
          for c in ler(TSE / 'votacao_secao_2026_PE/votacao_secao_2026_PE.csv', usecols=cols, chunksize=1_000_000)]
v = pd.concat(partes)
v.columns = [c.lower() for c in v.columns]
v['cargo'] = v.ds_cargo.str.upper().map(CARGOS)
v['qt_votos'] = v.qt_votos.astype(int)
v['partido'] = v.nr_votavel.str[:2]
v['bloco'] = v.partido.map(partido_bloco).fillna('O')
ajuste = {n: b for n, (b, _) in AJUSTES.items()}
nominal = v.nr_votavel.str.len() > 2
v.loc[nominal & v.nr_votavel.isin(ajuste), 'bloco'] = v.nr_votavel.map(ajuste)
v.loc[v.nr_votavel == BRANCO, 'bloco'] = 'branco'
v.loc[v.nr_votavel == NULO, 'bloco'] = 'nulo'

sec = v.pivot_table(index=['cargo', 'nr_zona', 'nr_secao', 'cd_municipio', 'nr_local_votacao'], columns='bloco',
                    values='qt_votos', aggfunc='sum', fill_value=0).reset_index()
sec.columns.name = None
sec['validos'] = sec[['R', 'J', 'O']].sum(axis=1)
sec.to_csv(SAIDA / 'deputados_secao.csv', index=False)
# votos nominais por candidato e seção (para o mais votado de cada lugar no mapa)
v[nominal][['cargo', 'nr_zona', 'nr_secao', 'cd_municipio', 'nr_local_votacao', 'nr_votavel', 'qt_votos']].to_csv(
    SAIDA / 'deputados_candidato_secao.csv', index=False)

# ---------------------------------------------------------------- candidatos
tot = v[nominal].groupby(['cargo', 'nr_votavel']).qt_votos.sum()
c = cand.assign(cargo=cand.DS_CARGO.str.upper().map(CARGOS))
c = c[['cargo', 'NR_CANDIDATO', 'NM_URNA_CANDIDATO', 'SG_PARTIDO', 'NR_PARTIDO', 'SG_FEDERACAO', 'NM_FEDERACAO', 'DS_SIT_TOT_TURNO']]
c.columns = ['cargo', 'nr_candidato', 'nome', 'partido', 'nr_partido', 'federacao', 'nome_federacao', 'situacao']
c['nome_federacao'] = c.nome_federacao.where(c.nome_federacao != '#NULO')   # partido fora de federação: vazio
# candidatura substituída (situação "#NULO") pode repetir o número de quem ficou: fica a válida
c = c.sort_values('situacao', key=lambda s: s.eq('#NULO')).drop_duplicates(['cargo', 'nr_candidato'])
c['bloco_coligacao'] = c.nr_partido.map(partido_bloco).fillna('O')
c['bloco'] = c.nr_candidato.map(ajuste).fillna(c.bloco_coligacao)
c['fonte_ajuste'] = c.nr_candidato.map({n: f for n, (_, f) in AJUSTES.items()})
c['votos'] = [tot.get((a, b), 0) for a, b in zip(c.cargo, c.nr_candidato)]
c['eleito'] = c.situacao.str.startswith('ELEITO')
c = c.sort_values(['cargo', 'votos'], ascending=[True, False])
c.to_csv(SAIDA / 'deputados_candidatos.csv', index=False)

# ---------------------------------------------------------------- resumo
for cargo, d in sec.groupby('cargo'):
    s = d[['R', 'J', 'O', 'branco', 'nulo', 'validos']].sum()
    e = c[(c.cargo == cargo) & c.eleito]
    print(f'\n{cargo}: {len(d)} seções; válidos {s.validos:,}; bloco Raquel {s.R / s.validos:.1%}, '
          f'bloco João {s.J / s.validos:.1%}, outros {s.O / s.validos:.1%}')
    print('  eleitos por bloco:', e.bloco.value_counts().to_dict(), '| total', len(e))
    print('  eleitos por partido:', e.groupby(['bloco', 'partido']).size().to_dict())
