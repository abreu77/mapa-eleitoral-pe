"""Exporta os dados do mapa (docs/data/) a partir de dados_limpos/.

Níveis: seção, local de votação, zona, município, RD, mesorregião, estado.
Eleições: 2022 T1, 2022 T2, 2026 T1 (governador). Base dos percentuais: votos totais.
Por unidade e eleição: total, Raquel, adversário (2022 T1: Danilo/PSB; 2022 T2: Marília;
2026: João), vencedor (código), e a variação de Raquel em 2026 contra 2022 T1 e T2
onde a unidade existe nas duas eleições.
Deputados estaduais (DE2026) e federais (DF2026): mesmo registro, com o bloco Raquel no lugar de
Raquel, o bloco João no lugar do adversário, o bloco mais votado como vencedor e o número do
candidato mais votado no lugar do nome; mais a diferença Raquel governadora menos bloco Raquel
(g: votos totais; gv: válidos). Blocos em src/deputados.py. Pontos em pontos_<nível>_dep.json.
Deputados eleitos (página deputado.html): votos de cada eleito por unidade em deputados/<cargo>_<número>.json.
Seções de voto em trânsito ficam fora dos pontos (não representam o bairro) e dentro dos agregados.
Rodar da raiz do projeto:  python src/exporta_mapa.py
"""
import json
import math
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
L = RAIZ / 'dados_limpos'
OUT = RAIZ / 'docs/data'
OUT.mkdir(parents=True, exist_ok=True)
TIPOS = {'nr_zona': str, 'nr_secao': str, 'cd_municipio': str, 'nr_local_votacao': str, 'nr_votavel': str}
ELEICOES = ['2022T1', '2022T2', '2026T1']
RAQUEL = {'2022T1': '45', '2022T2': '45', '2026T1': '55'}
ADVERSARIO = {'2022T1': '40', '2022T2': '77', '2026T1': '40'}
# vencedor em categorias com no máximo 3 cores no mapa (regra de cor para mapas)
CAT = {'2022T1': {'45': 'R', '77': 'M'}, '2022T2': {'45': 'R', '77': 'M'}, '2026T1': {'55': 'R', '40': 'J'}}
DEP = {'DE2026': 'estadual', 'DF2026': 'federal', 'SE2026': 'senador'}
N_MAPA_SENADO = 6   # senado: mapa individual dos 6 mais votados (decisão do Diego); deputados: só os eleitos

sec = pd.read_csv(L / 'secoes.csv', dtype=TIPOS)
lon = pd.read_csv(L / 'votos_secao_longo.csv', dtype=TIPOS)
mun = pd.read_csv(L / 'municipios.csv', dtype={'cd_tse': str, 'cd_ibge': str})
cand = pd.read_csv(L / 'candidatos.csv', dtype={'nr_votavel': str})
nomes = {(r.eleicao, r.nr_votavel): r.nm_votavel.title() for r in cand.itertuples()}

info = sec[['eleicao', 'nr_zona', 'nr_secao', 'cd_municipio', 'nr_local_votacao', 'nm_local_votacao',
            'nm_bairro', 'lat', 'lon', 'transito', 'aptos']]
lon = lon.merge(info[['eleicao', 'nr_zona', 'nr_secao', 'nr_local_votacao', 'transito']],
                on=['eleicao', 'nr_zona', 'nr_secao', 'nr_local_votacao'], how='left')
lon = lon.merge(mun[['cd_tse', 'nm_municipio', 'rd', 'mesorregiao']], left_on='cd_municipio', right_on='cd_tse')
lon['estado'] = 'Pernambuco'
lon['local_id'] = lon.nr_zona + '-' + lon.nr_local_votacao
lon['secao_id'] = lon.nr_zona + '-' + lon.nr_secao



def chaves(d):
    """Colunas de agregação (seção, local, RD, mesorregião, estado) e marca de trânsito, como em lon."""
    d = d.merge(info.loc[info.eleicao == '2026T1', ['nr_zona', 'nr_secao', 'transito']], on=['nr_zona', 'nr_secao'], how='left')
    d = d.merge(mun[['cd_tse', 'rd', 'mesorregiao']], left_on='cd_municipio', right_on='cd_tse')
    d['estado'] = 'Pernambuco'
    d['local_id'] = d.nr_zona + '-' + d.nr_local_votacao
    d['secao_id'] = d.nr_zona + '-' + d.nr_secao
    return d


dsec = chaves(pd.read_csv(L / 'deputados_secao.csv', dtype=TIPOS))
dcan = chaves(pd.read_csv(L / 'deputados_candidato_secao.csv', dtype=TIPOS))
dcand = pd.read_csv(L / 'deputados_candidatos.csv', dtype={'nr_candidato': str})

NIVEIS = {'secao': 'secao_id', 'local': 'local_id', 'zona': 'nr_zona', 'municipio': 'cd_municipio',
          'rd': 'rd', 'meso': 'mesorregiao', 'estado': 'estado'}


def metricas(nivel, chave):
    out = {}
    for el in ELEICOES:
        v = lon[lon.eleicao == el]
        if nivel in ('secao', 'local'):
            v = v[~v.transito.fillna(False).astype(bool)]
        p = v.pivot_table(index=chave, columns='nr_votavel', values='qt_votos', aggfunc='sum', fill_value=0)
        tot = p.sum(axis=1)
        cands = [c for c in p.columns if c not in ('95', '96')]
        top = p[cands].idxmax(axis=1)
        empate = p[cands].eq(p[cands].max(axis=1), axis=0).sum(axis=1) > 1
        venc = top.map(lambda c: CAT[el].get(c, 'O')).where(~empate, 'E')
        df = pd.DataFrame({'t': tot, 'w': p[cands].sum(axis=1), 'r': p[RAQUEL[el]], 'a': p[ADVERSARIO[el]], 'v': venc,
                           'vn': top.map(lambda c: nomes.get((el, c), c)).where(~empate, 'Empate')})
        out[el] = df
    gov = out['2026T1']
    for el, cargo in DEP.items():
        s, c = dsec[dsec.cargo == cargo], dcan[dcan.cargo == cargo]
        if nivel in ('secao', 'local'):
            s, c = s[~s.transito.fillna(False).astype(bool)], c[~c.transito.fillna(False).astype(bool)]
        g = s.groupby(chave)[['R', 'J', 'O', 'branco', 'nulo', 'validos']].sum()
        b = g[['R', 'J', 'O']]
        empate = b.eq(b.max(axis=1), axis=0).sum(axis=1) > 1
        cc = c.groupby([chave, 'nr_votavel']).qt_votos.sum().reset_index()
        mx = cc.groupby(chave).qt_votos.transform('max')
        topo = cc[cc.qt_votos == mx].groupby(chave).nr_votavel.agg(lambda x: x.iat[0] if len(x) == 1 else '')  # '' = empate
        df = pd.DataFrame({'t': g[['R', 'J', 'O', 'branco', 'nulo']].sum(axis=1), 'w': g.validos, 'r': g.R, 'a': g.J,
                           'v': b.idxmax(axis=1).where(~empate, 'E'), 'vn': topo.reindex(g.index).fillna('')})
        gv = gov.reindex(df.index)
        df['g'] = gv.r / gv.t * 100 - df.r / df.t * 100                          # Raquel governadora menos bloco Raquel
        df['gv'] = gv.r / gv.w * 100 - df.r / df.w.where(df.w > 0) * 100
        out[el] = df
    return out


def arred(x, n=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)


def registros(nivel, chave):
    m = metricas(nivel, chave)
    pct = {el: (m[el].r / m[el].t * 100) for el in ELEICOES}                       # base: votos totais
    pctv = {el: (m[el].r / m[el].w.where(m[el].w > 0) * 100) for el in ELEICOES}   # base: votos válidos
    linhas = {}
    for el, d in m.items():
        for k, r in d.iterrows():
            linhas.setdefault(k, {})[el] = [int(r.t), int(r.r), int(r.a), r.v, r.vn, int(r.w)] + \
                ([arred(r.g), arred(r.gv)] if el in DEP else [])
    for k, l in linhas.items():
        for sufixo, base in (('', pct), ('v', pctv)):
            p26 = base['2026T1'].get(k)
            l['d1' + sufixo] = arred(p26 - base['2022T1'].get(k)) if p26 is not None and k in base['2022T1'] else None
            l['d2' + sufixo] = arred(p26 - base['2022T2'].get(k)) if p26 is not None and k in base['2022T2'] else None
    return linhas


# ---------------------------------------------------------------- polígonos (município e acima)
pol = {}
for nivel in ('municipio', 'rd', 'meso', 'estado'):
    pol[nivel] = registros(nivel, NIVEIS[nivel])
nome_mun = mun.set_index('cd_tse')
# aliança do prefeito: lista do Jamildo.com (estado em 06/10/2026), com crédito no site
LADO = {'Raquel Lyra': 'R', 'João Campos': 'J'}
mun_meta = {r.cd_tse: {'nome': r.nm_municipio, 'ibge': r.cd_ibge, 'rd': r.rd, 'meso': r.mesorregiao,
                       'alianca': LADO.get(r.alianca_prefeito, 'N'),
                       'prefeito': r.prefeito if isinstance(r.prefeito, str) else None,
                       'partido': r.partido_prefeito if isinstance(r.partido_prefeito, str) else None}
            for r in mun.itertuples()}
# candidatos a deputado: número -> [nome de urna, partido, bloco, eleito, votos, fonte do ajuste de bloco,
#                                   federação (nome do TSE ou None), bloco do partido na coligação de governador]
def com_mapa(cargo):
    d = dcand[dcand.cargo == cargo]
    return list(d.nlargest(N_MAPA_SENADO, 'votos').nr_candidato if cargo == 'senador' else d[d.eleito].nr_candidato)


mapas = {el: com_mapa(cargo) for el, cargo in DEP.items()}
#                                   ..., 1 se tem mapa individual (deputado.html)
cands = {el: {r.nr_candidato: [r.nome, r.partido, r.bloco, int(r.eleito), int(r.votos),
                               r.fonte_ajuste if isinstance(r.fonte_ajuste, str) else None,
                               r.nome_federacao if isinstance(r.nome_federacao, str) else None, r.bloco_coligacao,
                               int(r.nr_candidato in mapas[el])]
              for r in dcand[dcand.cargo == cargo].itertuples()} for el, cargo in DEP.items()}
(OUT / 'agregados.json').write_text(json.dumps({'municipio': pol['municipio'], 'rd': pol['rd'], 'meso': pol['meso'],
                                                'estado': pol['estado'], 'municipios_meta': mun_meta,
                                                'candidatos': cands},
                                               ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

# ---------------------------------------------------------------- pontos (seção, local, zona) por eleição
pos = info[~info.transito.fillna(False).astype(bool)].dropna(subset=['lat'])
pontos = {}
ordem = {}   # nível -> eleição -> ids na ordem das linhas (os arquivos dos eleitos seguem essa ordem)
for nivel in ('secao', 'local', 'zona'):
    reg = registros(nivel, NIVEIS[nivel])
    por_el = {}
    for el in ELEICOES + list(DEP):
        p = pos[pos.eleicao == (el if el in ELEICOES else '2026T1')].copy()
        p['local_id'] = p.nr_zona + '-' + p.nr_local_votacao
        p['secao_id'] = p.nr_zona + '-' + p.nr_secao
        if nivel == 'secao':
            # seções do mesmo local dividem a coordenada: abre em anel pequeno (~12 m por seção)
            p['k'] = p.groupby('local_id').cumcount()
            p['n'] = p.groupby('local_id').secao_id.transform('count')
            ang = 2 * math.pi * p.k / p.n.clip(lower=1)
            raio = 0.00011 * (p.n.clip(lower=2) ** 0.5)
            p['plat'] = p.lat + raio * ang.map(math.sin) * (p.n > 1)
            p['plon'] = p.lon + raio * ang.map(math.cos) * (p.n > 1) / math.cos(math.radians(-8.3))
            g = p.set_index('secao_id')
            itens = [(k, r.plon, r.plat, '', r.nm_local_votacao, r.cd_municipio)   # título montado no site pelo id
                     for k, r in g.iterrows()]
        elif nivel == 'local':
            g = p.groupby('local_id').agg(lat=('lat', 'first'), lon=('lon', 'first'), nome=('nm_local_votacao', 'first'),
                                          bairro=('nm_bairro', 'first'), zona=('nr_zona', 'first'), mun=('cd_municipio', 'first'))
            itens = [(k, r.lon, r.lat, r.nome, f'{r.bairro} · Zona {r.zona}', r.mun) for k, r in g.iterrows()]
        else:
            w = p.assign(a=p.aptos.fillna(0))
            g = w.groupby('nr_zona').apply(lambda d: pd.Series({
                'lat': (d.lat * d.a).sum() / d.a.sum(), 'lon': (d.lon * d.a).sum() / d.a.sum(),
                'mun': d.cd_municipio.mode().iat[0]}), include_groups=False)
            itens = [(k, r.lon, r.lat, f'Zona eleitoral {k}', 'Ponto no centro dos locais de votação da zona', r.mun)
                     for k, r in g.iterrows()]
        linhas, textos, idx = [], [], {}

        def ref(s):   # textos repetidos (nome do local, bairro) viram índice numa tabela
            if s not in idx:
                idx[s] = len(textos)
                textos.append(s)
            return idx[s]

        for k, x, y, nome, sub, cd in itens:
            r = reg.get(k, {})
            if el not in r:
                continue
            if el in DEP:   # mesma posição dos campos; no lugar do nome, o número do candidato mais votado
                t_, r_, a_, v_, vn_, w_, g_, gv_ = r[el]
                linhas.append([round(x, 5), round(y, 5), ref(nome), ref(sub), cd, k, t_, r_, a_, v_,
                               vn_, None, None, w_, None, None, g_, gv_])
                continue
            t_, r_, a_, v_, vn_, w_ = r[el]
            linhas.append([round(x, 5), round(y, 5), ref(nome), ref(sub), cd, k, t_, r_, a_, v_,
                           ref(vn_) if v_ == 'O' else -1, r.get('d1'), r.get('d2'), w_, r.get('d1v'), r.get('d2v')])
        por_el[el] = {'textos': textos, 'linhas': linhas}
    for arq, els in ((f'pontos_{nivel}.json', ELEICOES), (f'pontos_{nivel}_dep.json', list(DEP))):
        (OUT / arq).write_text(json.dumps({el: por_el[el] for el in els}, ensure_ascii=False, separators=(',', ':')),
                               encoding='utf-8')
    pontos[nivel] = {el: len(v['linhas']) for el, v in por_el.items()}
    ordem[nivel] = {el: [l[5] for l in por_el[el]['linhas']] for el in DEP}

# ---------------------------------------------------------------- um arquivo por candidato com mapa (deputado.html)
# deputados eleitos e os 6 mais votados para o senado; votos por unidade; seção, local e zona em lista
# na ordem de pontos_<nível>_dep.json
DIR_DEP = OUT / 'deputados'
DIR_DEP.mkdir(exist_ok=True)
for el, cargo in DEP.items():
    eleitos = mapas[el]
    c = dcan[(dcan.cargo == cargo) & dcan.nr_votavel.isin(eleitos)]
    sem_transito = c[~c.transito.fillna(False).astype(bool)]
    por = {nivel: (sem_transito if nivel in ('secao', 'local') else c).groupby(['nr_votavel', chave]).qt_votos.sum()
           for nivel, chave in NIVEIS.items()}
    for nr in eleitos:
        arq = {}
        for nivel in NIVEIS:
            v = por[nivel].loc[nr]
            arq[nivel] = ([int(v.get(k, 0)) for k in ordem[nivel][el]] if nivel in ordem
                          else {k: int(x) for k, x in v.items()})
        assert arq['estado']['Pernambuco'] == int(dcand[(dcand.cargo == cargo) & (dcand.nr_candidato == nr)].votos.iat[0])
        (DIR_DEP / f'{el}_{nr}.json').write_text(json.dumps(arq, separators=(',', ':')), encoding='utf-8')

# ---------------------------------------------------------------- malha municipal com cd_tse
DADOS = next(p for p in RAIZ.parents if (p / 'dados-ibge').is_dir())   # estudos-dados/ (vale também numa worktree)
geo = json.loads((DADOS / 'dados-ibge/malha_municipios_PE.geojson').read_text(encoding='utf-8'))
ibge2tse = {r.cd_ibge: r.cd_tse for r in mun.itertuples()}
for f in geo['features']:
    f['properties'] = {'id': ibge2tse[f['properties']['codarea']]}
(OUT / 'municipios.geojson').write_text(json.dumps(geo, separators=(',', ':')), encoding='utf-8')

print('pontos:', pontos)
print('agregados:', {k: len(v) for k, v in pol.items()})
e = pol['estado']['Pernambuco']
print('estado, conferência (total, Raquel, adversário, válidos):', {el: [e[el][i] for i in (0, 1, 2, 5)] for el in ELEICOES})
for el in DEP:
    print(el, 'estado (total, bloco Raquel, bloco João, vencedor, mais votado, válidos, g, gv):', e[el])
print('Raquel % válidos:', {el: round(e[el][1] / e[el][5] * 100, 2) for el in ELEICOES}, '| variação 2026 x T2 em válidos:', e['d2v'])
for f in sorted(OUT.iterdir()):
    if f.is_file():
        print(f.name, round(f.stat().st_size / 1e6, 2), 'MB')
print('deputados/:', len(list(DIR_DEP.iterdir())), 'arquivos,', round(sum(f.stat().st_size for f in DIR_DEP.iterdir()) / 1e6, 2), 'MB')
