"""Exporta os dados do mapa (site/data/) a partir de dados_limpos/.

Níveis: seção, local de votação, zona, município, RD, mesorregião, estado.
Eleições: 2022 T1, 2022 T2, 2026 T1 (governador). Base dos percentuais: votos totais.
Por unidade e eleição: total, Raquel, adversário (2022 T1: Danilo/PSB; 2022 T2: Marília;
2026: João), vencedor (código), e a variação de Raquel em 2026 contra 2022 T1 e T2
onde a unidade existe nas duas eleições.
Seções de voto em trânsito ficam fora dos pontos (não representam o bairro) e dentro dos agregados.
Rodar da raiz do projeto:  python src/exporta_mapa.py
"""
import json
import math
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
L = RAIZ / 'dados_limpos'
OUT = RAIZ / 'site/data'
OUT.mkdir(parents=True, exist_ok=True)
TIPOS = {'nr_zona': str, 'nr_secao': str, 'cd_municipio': str, 'nr_local_votacao': str, 'nr_votavel': str}
ELEICOES = ['2022T1', '2022T2', '2026T1']
RAQUEL = {'2022T1': '45', '2022T2': '45', '2026T1': '55'}
ADVERSARIO = {'2022T1': '40', '2022T2': '77', '2026T1': '40'}
# vencedor em categorias com no máximo 3 cores no mapa (regra de cor para mapas)
CAT = {'2022T1': {'45': 'R', '77': 'M'}, '2022T2': {'45': 'R', '77': 'M'}, '2026T1': {'55': 'R', '40': 'J'}}

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
    return out


def arred(x, n=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)


def registros(nivel, chave):
    m = metricas(nivel, chave)
    pct = {el: (d.r / d.t * 100) for el, d in m.items()}                       # base: votos totais
    pctv = {el: (d.r / d.w.where(d.w > 0) * 100) for el, d in m.items()}       # base: votos válidos
    linhas = {}
    for el, d in m.items():
        for k, r in d.iterrows():
            linhas.setdefault(k, {})[el] = [int(r.t), int(r.r), int(r.a), r.v, r.vn, int(r.w)]
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
(OUT / 'agregados.json').write_text(json.dumps({'municipio': pol['municipio'], 'rd': pol['rd'], 'meso': pol['meso'],
                                                'estado': pol['estado'], 'municipios_meta': mun_meta},
                                               ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

# ---------------------------------------------------------------- pontos (seção, local, zona) por eleição
pos = info[~info.transito.fillna(False).astype(bool)].dropna(subset=['lat'])
pontos = {}
for nivel in ('secao', 'local', 'zona'):
    reg = registros(nivel, NIVEIS[nivel])
    por_el = {}
    for el in ELEICOES:
        p = pos[pos.eleicao == el].copy()
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
            t_, r_, a_, v_, vn_, w_ = r[el]
            linhas.append([round(x, 5), round(y, 5), ref(nome), ref(sub), cd, k, t_, r_, a_, v_,
                           ref(vn_) if v_ == 'O' else -1, r.get('d1'), r.get('d2'), w_, r.get('d1v'), r.get('d2v')])
        por_el[el] = {'textos': textos, 'linhas': linhas}
    (OUT / f'pontos_{nivel}.json').write_text(json.dumps(por_el, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    pontos[nivel] = {el: len(v['linhas']) for el, v in por_el.items()}

# ---------------------------------------------------------------- malha municipal com cd_tse
geo = json.loads((RAIZ.parent / 'dados-ibge/malha_municipios_PE.geojson').read_text(encoding='utf-8'))
ibge2tse = {r.cd_ibge: r.cd_tse for r in mun.itertuples()}
for f in geo['features']:
    f['properties'] = {'id': ibge2tse[f['properties']['codarea']]}
(OUT / 'municipios.geojson').write_text(json.dumps(geo, separators=(',', ':')), encoding='utf-8')

print('pontos:', pontos)
print('agregados:', {k: len(v) for k, v in pol.items()})
e = pol['estado']['Pernambuco']
print('estado, conferência (total, Raquel, adversário, válidos):', {el: [e[el][i] for i in (0, 1, 2, 5)] for el in ELEICOES})
print('Raquel % válidos:', {el: round(e[el][1] / e[el][5] * 100, 2) for el in ELEICOES}, '| variação 2026 x T2 em válidos:', e['d2v'])
for f in sorted(OUT.iterdir()):
    print(f.name, round(f.stat().st_size / 1e6, 2), 'MB')
