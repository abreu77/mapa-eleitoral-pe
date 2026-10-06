/* Mapa eleitoral de Pernambuco, governador 2022–2026.
   Dados gerados por src/exporta_mapa.py em data/. Percentuais sobre votos totais. */
'use strict';

const NIVEIS = ['secao', 'local', 'zona', 'municipio', 'rd', 'meso', 'estado'];
const NIVEL_NOME = ['Seção', 'Local de votação', 'Zona eleitoral', 'Município', 'Região de Desenvolvimento', 'Mesorregião', 'Estado'];
const ELEICAO_NOME = { '2022T1': '2022 · 1º turno', '2022T2': '2022 · 2º turno', '2026T1': '2026' };
const ADV = { '2022T1': 'Danilo Cabral (PSB)', '2022T2': 'Marília Arraes', '2026T1': 'João Campos' };
const CAT_NOME = { R: 'Raquel Lyra', J: 'João Campos', M: 'Marília Arraes', O: 'Outro candidato', E: 'Empate' };
const CAT_ORDEM = { '2022T1': ['R', 'M', 'O', 'E'], '2022T2': ['R', 'M', 'E'], '2026T1': ['R', 'J', 'E'] };

/* escalas (classes fixas para comparar eleições com a mesma régua) */
const ESC = {
  pct: { limites: [10, 20, 30, 40, 50, 60, 70],
    claro: ['#efecf8', '#dcd5f1', '#c3b8e6', '#a697d9', '#8875ca', '#6b55b8', '#5240a3', '#3b2c85'],
    escuro: ['#241d45', '#31275f', '#40347c', '#52449a', '#6656b6', '#7d6dcd', '#9787df', '#b4a8ee'] },
  dif: { limites: [-30, -15, -5, -2, 2, 5, 15, 30],
    claro: ['#a87400', '#d39a00', '#f0c24a', '#f7dd96', '#e9e9e6', '#d6cff0', '#ad9fdf', '#7a67c6', '#4a3aa7'],
    escuro: ['#e3a21a', '#b88316', '#8a6416', '#5a4619', '#383835', '#3e3666', '#55489a', '#7466c9', '#9f93ef'] },
  var: { limites: [-20, -10, -5, -1, 1, 5, 10, 20],
    claro: ['#1f6b2a', '#3f9147', '#80bd84', '#c5e2c5', '#e9e9e6', '#d6cff0', '#ad9fdf', '#7a67c6', '#4a3aa7'],
    escuro: ['#74c97b', '#4f9d56', '#356d3b', '#26432a', '#383835', '#3e3666', '#55489a', '#7466c9', '#9f93ef'] },
};

const estado = { eleicao: '2026T1', leitura: 'pct', base: 'd2', denom: 't', nivel: 3, foco: null };
const dados = { agregados: null, municipiosGeo: null, pontos: {}, poligonos: {} };
const $ = (s) => document.querySelector(s);
const fmtInt = new Intl.NumberFormat('pt-BR');
const fmtPct = (x) => (x == null || Number.isNaN(x) ? '—' : x.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%');
const fmtPp = (x) => (x == null || Number.isNaN(x) ? '—' : (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(x).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' p.p.');

// tema fixo no claro (decisão do Diego): o modo escuro do sistema não muda o mapa
const escuro = () => false;
const cor = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const corCat = (c) => ({ R: cor('--raquel'), J: cor('--joao'), M: cor('--marilia'), O: cor('--outro'), E: cor('--empate') }[c] || cor('--sem-dado'));
function classe(valor, esc) {
  const cores = escuro() ? esc.escuro : esc.claro;
  if (valor == null || Number.isNaN(valor)) return cor('--sem-dado');
  let i = esc.limites.findIndex((l) => valor < l);
  if (i === -1) i = esc.limites.length;
  return cores[i];
}

/* nome de urna para os três principais; demais candidatos com o nome do TSE, preposições em minúscula */
function nomeVencedor(v, vn) {
  if (v !== 'O') return CAT_NOME[v] || vn;
  return String(vn).replace(/(De|Da|Do|Dos|Das|E)/g, (m) => m.toLowerCase());
}

const LADO_NOME = { R: 'com Raquel Lyra', J: 'com João Campos', N: 'sem prefeito' };
function prefeitoHTML(cd) {
  const m = dados.agregados?.municipios_meta?.[cd];
  if (!m) return '';
  if (m.alianca === 'N') return `<p class="prefeito"><i style="background:${cor('--sem-dado')}"></i>Sem prefeito (distrito estadual)</p>`;
  return `<p class="prefeito"><i style="background:${corCat(m.alianca)}"></i>Prefeito ${m.prefeito}${m.partido ? ` (${m.partido})` : ''} · ${LADO_NOME[m.alianca]}</p>`;
}

/* registro de uma unidade: [total, raquel, adversário, vencedor, nome do vencedor] por eleição; d1, d2 = variação */
function valores(reg, el) {
  const r = reg && reg[el];
  if (!r) return null;
  const [t, rq, a, v, vn, w] = r;
  const válidos = estado.denom === 'w';
  const den = válidos ? w : t;   // base escolhida: votos totais (t) ou válidos (w)
  return { t, w, n: den, rq, a, v, vn: nomeVencedor(v, vn), pr: den ? (rq / den) * 100 : null, pa: den ? (a / den) * 100 : null,
    d1: válidos ? reg.d1v : reg.d1, d2: válidos ? reg.d2v : reg.d2 };
}
function valorLeitura(v) {
  if (!v) return null;
  if (estado.leitura === 'pct') return v.pr;
  if (estado.leitura === 'dif') return estado.eleicao === '2022T2' ? null : v.pr - v.pa;
  if (estado.leitura === 'var') return v[estado.base];
  return null;
}
function corDe(v) {
  if (!v) return cor('--sem-dado');
  if (estado.leitura === 'venc') return corCat(v.v);
  return classe(valorLeitura(v), ESC[estado.leitura]);
}

/* ---------------------------------------------------------------- carga */
async function json(url) { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }

async function pontos(nivel) {
  if (!dados.pontos[nivel]) {
    $('#carregando').hidden = nivel !== 'secao';
    dados.pontos[nivel] = await json(`data/pontos_${nivel}.json`);
    $('#carregando').hidden = true;
  }
  return dados.pontos[nivel];
}

function poligonos(nivel) {
  if (dados.poligonos[nivel]) return dados.poligonos[nivel];
  const meta = dados.agregados.municipios_meta;
  const feats = dados.municipiosGeo.features;
  let fc;
  if (nivel === 'municipio') {
    fc = feats.map((f) => ({ type: 'Feature', geometry: f.geometry, properties: { id: f.properties.id, nome: meta[f.properties.id].nome } }));
  } else {
    const grupos = {};
    for (const f of feats) {
      const k = nivel === 'estado' ? 'Pernambuco' : meta[f.properties.id][nivel === 'rd' ? 'rd' : 'meso'];
      (grupos[k] ||= []).push(f);
    }
    fc = Object.entries(grupos).map(([k, fs]) => {
      const u = fs.length === 1 ? fs[0] : turf.union(turf.featureCollection(fs));
      return { type: 'Feature', geometry: u.geometry, properties: { id: k, nome: k } };
    });
  }
  return (dados.poligonos[nivel] = fc);
}

/* ---------------------------------------------------------------- mapa */
/* mapa de fundo: OpenFreeMap (gratuito, sem chave), estilos Positron (claro) e Dark */
const mapa = new maplibregl.Map({
  container: 'mapa',
  style: `https://tiles.openfreemap.org/styles/${escuro() ? 'dark' : 'positron'}`,
  bounds: [[-41.4, -9.55], [-34.75, -7.25]],
  fitBoundsOptions: { padding: 24 },
  attributionControl: { compact: true },
  dragRotate: false, pitchWithRotate: false,
});
mapa.touchZoomRotate.disableRotation();
mapa.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10, maxWidth: '280px' });

function camadas() {
  const antes = mapa.getStyle().layers.find((l) => l.type === 'symbol')?.id;   // dados ficam abaixo dos rótulos
  mapa.addSource('area', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, promoteId: 'id' });
  mapa.addSource('contorno', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  mapa.addSource('pontos', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  mapa.addLayer({ id: 'area', type: 'fill', source: 'area', paint: { 'fill-color': ['get', 'c'], 'fill-opacity': 0.9 } }, antes);
  // limites: claros no escuro e brancos no claro, mais grossos com o zoom e nos níveis RD e meso
  mapa.addLayer({ id: 'area-linha', type: 'line', source: 'area', paint: {
    'line-color': escuro() ? 'rgba(237,241,247,0.55)' : 'rgba(255,255,255,0.95)',
    'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.7, 9, 1.2, 12, 1.8],
  } }, antes);
  mapa.addLayer({ id: 'contorno', type: 'line', source: 'contorno', paint: {
    'line-color': escuro() ? 'rgba(237,241,247,0.32)' : 'rgba(13,31,60,0.32)',
    'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.6, 12, 1.2],
  } }, antes);
  mapa.addSource('limite', { type: 'geojson', data: { type: 'FeatureCollection', features: poligonos('estado') } });
  mapa.addLayer({ id: 'limite', type: 'line', source: 'limite', paint: {
    'line-color': escuro() ? '#edf1f7' : '#0c2856', 'line-opacity': 0.85,
    'line-width': ['interpolate', ['linear'], ['zoom'], 6, 1.4, 10, 2.2],
  } }, antes);
  mapa.addLayer({ id: 'pontos', type: 'circle', source: 'pontos', paint: {
    'circle-color': ['get', 'c'],
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, ['*', ['get', 's'], 0.55], 10, ['*', ['get', 's'], 1.3], 14, ['*', ['get', 's'], 3.2]],
    'circle-stroke-color': escuro() ? 'rgba(10,19,34,0.9)' : 'rgba(13,31,60,0.45)',
    'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 6, 0.3, 12, 0.8],
  } }, antes);
  mapa.addLayer({ id: 'foco', type: 'line', source: 'area', filter: ['==', ['get', 'id'], ''], paint: { 'line-color': escuro() ? '#edf1f7' : '#0c2856', 'line-width': 2 } }, antes);

  for (const camada of ['area', 'pontos']) {
    mapa.on('mousemove', camada, (e) => { mapa.getCanvas().style.cursor = 'pointer'; mostraPopup(e.features[0], e.lngLat); });
    mapa.on('mouseleave', camada, () => { mapa.getCanvas().style.cursor = ''; popup.remove(); });
    mapa.on('click', camada, (e) => { estado.foco = e.features[0].properties.id; atualizaFoco(); destacaFoco(); });
  }
}

/* ---------------------------------------------------------------- desenho */
let registroAtual = {};   // id -> registro (todas as eleições) do nível atual
let titulos = {};         // id -> [título, subtítulo]

async function desenha() {
  const nivel = NIVEIS[estado.nivel];
  const ag = dados.agregados;
  registroAtual = {}; titulos = {}; popup.remove();
  if (['municipio', 'rd', 'meso', 'estado'].includes(nivel)) {
    const regs = ag[nivel];
    const fc = poligonos(nivel).map((f) => {
      const v = valores(regs[f.properties.id], estado.eleicao);
      registroAtual[f.properties.id] = regs[f.properties.id];
      const corPref = estado.leitura === 'pref' ? corCat(ag.municipios_meta[f.properties.id].alianca === 'N' ? 'X' : ag.municipios_meta[f.properties.id].alianca) : null;
      titulos[f.properties.id] = [f.properties.nome, nivel === 'municipio' ? ag.municipios_meta[f.properties.id].rd : NIVEL_NOME[estado.nivel]];
      return { ...f, properties: { ...f.properties, c: corPref || corDe(v) } };
    });
    mapa.getSource('area').setData({ type: 'FeatureCollection', features: fc });
    const fator = nivel === 'municipio' ? 1 : 2;
    mapa.setPaintProperty('area-linha', 'line-width', ['interpolate', ['linear'], ['zoom'], 6, 0.7 * fator, 9, 1.2 * fator, 12, 1.8 * fator]);
    mapa.getSource('pontos').setData({ type: 'FeatureCollection', features: [] });
    mapa.getSource('contorno').setData({ type: 'FeatureCollection', features: [] });
  } else {
    const p = await pontos(nivel);
    if (NIVEIS[estado.nivel] !== nivel) return;   // o usuário mudou de nível durante a carga
    const bloco = p[estado.eleicao];
    const meta = ag.municipios_meta;
    const base = nivel === 'secao' ? 2.2 : nivel === 'local' ? 0.16 : 0.035;
    const feats = bloco.linhas.map((l) => {
      const [x, y, iNome, iSub, cd, id, t, rq, a, v, iVn, d1, d2, w, d1v, d2v] = l;
      const reg = { [estado.eleicao]: [t, rq, a, v, iVn >= 0 ? bloco.textos[iVn] : CAT_NOME[v], w], d1, d2, d1v, d2v };
      registroAtual[id] = reg;
      const titulo = nivel === 'secao' ? `Seção ${id.split('-')[1]} · Zona ${id.split('-')[0]}` : bloco.textos[iNome];
      titulos[id] = [titulo, `${bloco.textos[iSub]}${meta[cd] ? ' · ' + meta[cd].nome : ''}`];
      const s = nivel === 'secao' ? base : base * Math.sqrt(t);
      return { type: 'Feature', geometry: { type: 'Point', coordinates: [x, y] }, properties: { id, c: corDe(valores(reg, estado.eleicao)), s } };
    });
    feats.sort((f, g) => g.properties.s - f.properties.s);   // pontos grandes por baixo
    mapa.getSource('pontos').setData({ type: 'FeatureCollection', features: feats });
    mapa.getSource('area').setData({ type: 'FeatureCollection', features: [] });
    mapa.getSource('contorno').setData({ type: 'FeatureCollection', features: poligonos('municipio') });
  }
  legenda(); atualizaFoco(); destacaFoco();
  if (!$('#tabela-area').hidden) tabela();
}

/* ---------------------------------------------------------------- legenda e textos */
function legenda() {
  const L = estado.leitura, el = estado.eleicao;
  const box = $('#legenda');
  const titulo = { pref: 'Prefeitos na disputa de 2026', pct: `% de Raquel Lyra · ${ELEICAO_NOME[el]}`, venc: `Mais votado · ${ELEICAO_NOME[el]}`,
    dif: `Raquel menos bloco PSB · ${ELEICAO_NOME[el]}`, var: `Raquel em 2026 menos ${estado.base === 'd2' ? '2022 · 2º turno' : '2022 · 1º turno'}` }[L];
  $('#legenda-titulo').textContent = titulo + (L === 'venc' ? '' : estado.denom === 'w' ? ' · válidos' : ' · totais');
  if (L === 'pref') {
    const n = Object.values(dados.agregados.municipios_meta).reduce((a, m) => (a[m.alianca] = (a[m.alianca] || 0) + 1, a), {});
    $('#legenda-titulo').textContent = 'Prefeitos na disputa de 2026';
    box.innerHTML = `<div class="cats">
      <div class="cat"><i style="background:${corCat('R')}"></i>Prefeito com Raquel Lyra · ${n.R} municípios</div>
      <div class="cat"><i style="background:${corCat('J')}"></i>Prefeito com João Campos · ${n.J} municípios</div>
      <div class="cat"><i style="background:${cor('--sem-dado')}"></i>Sem prefeito · Fernando de Noronha</div></div>
      <p class="fonte">Fonte: Jamildo.com, estado em 06/10/2026.</p>`;
    return;
  }
  if (L === 'venc') {
    box.innerHTML = `<div class="cats">${CAT_ORDEM[el].map((c) => `<div class="cat"><i style="background:${corCat(c)}"></i>${CAT_NOME[c]}</div>`).join('')}</div>`;
    return;
  }
  const esc = ESC[L]; const cores = escuro() ? esc.escuro : esc.claro;
  // um rótulo por faixa, alinhado à faixa: limite inferior (a primeira faixa diz "até")
  const sinal = (x) => (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(x);
  const rotulos = cores.map((_, i) => {
    if (L === 'pct') return i === 0 ? '<10' : i === cores.length - 1 ? '70+' : String(esc.limites[i - 1]);
    if (i === 0) return '<' + sinal(esc.limites[0]);
    if (i === cores.length - 1) return sinal(esc.limites[i - 1]) + '+';
    return sinal(esc.limites[i - 1]);
  });
  const pontas = { pct: ['menos Raquel', 'mais Raquel (%)'], dif: [`${ADV[el].replace(' (PSB)', '')} à frente`, 'Raquel à frente (p.p.)'], var: ['Raquel caiu', 'Raquel subiu (p.p.)'] }[L];
  box.innerHTML = `<div class="escala">${cores.map((c) => `<span style="background:${c}"></span>`).join('')}</div>
    <div class="escala escala-rotulos">${rotulos.map((r) => `<em>${r}</em>`).join('')}</div>
    <div class="escala-pontas"><span>${pontas[0]}</span><span>${pontas[1]}</span></div>`;
}

function linhaPop(nome, corBola, valor) {
  return `<div class="pop-linha"><span>${corBola ? `<i style="background:${corBola}"></i>` : ''}${nome}</span><span>${valor}</span></div>`;
}
function mostraPopup(f, lngLat) {
  const id = f.properties.id;
  const v = valores(registroAtual[id], estado.eleicao);
  const [t, sub] = titulos[id] || [id, ''];
  let corpo = '';
  if (v) {
    corpo += linhaPop('Raquel Lyra', corCat('R'), fmtPct(v.pr));
    corpo += linhaPop(ADV[estado.eleicao], corCat(estado.eleicao === '2026T1' ? 'J' : estado.eleicao === '2022T2' ? 'M' : 'O'), fmtPct(v.pa));
    if (estado.leitura === 'var') corpo += linhaPop('Variação de Raquel', '', fmtPp(v[estado.base]));
    corpo += linhaPop('Mais votado', '', v.vn);
    corpo += linhaPop(estado.denom === 'w' ? 'Votos válidos' : 'Votos totais', '', fmtInt.format(v.n));
  } else corpo = '<p class="pop-sub">Sem dado nesta eleição.</p>';
  const pref = NIVEIS[estado.nivel] === 'municipio' ? prefeitoHTML(id) : '';
  popup.setLngLat(lngLat).setHTML(`<p class="pop-titulo">${t}</p><p class="pop-sub">${sub}</p>${pref}${corpo}`).addTo(mapa);
}

function atualizaFoco() {
  const el = estado.eleicao;
  const reg = estado.foco && registroAtual[estado.foco] ? registroAtual[estado.foco] : dados.agregados.estado.Pernambuco;
  const nome = estado.foco && titulos[estado.foco] ? titulos[estado.foco][0] : 'Pernambuco';
  const v = valores(reg, el);
  $('#foco-rotulo').textContent = nome;
  if (!v) { $('#foco').innerHTML = '<p class="meta">Sem dado nesta eleição.</p>'; return; }
  const outros = Math.max(0, 100 - v.pr - v.pa);   // outros candidatos (+ brancos e nulos, na base total)
  const corAdv = corCat(el === '2026T1' ? 'J' : el === '2022T2' ? 'M' : 'O');
  const extra = estado.leitura === 'var'
    ? `<div class="num"><b>${fmtPp(v[estado.base])}</b><span>Raquel em 2026 menos ${estado.base === 'd2' ? '2022 · 2º turno' : '2022 · 1º turno'}</span></div>`
    : `<div class="num"><b>${fmtInt.format(v.n)}</b><span>${estado.denom === 'w' ? 'votos válidos' : 'votos totais'}</span></div>`;
  $('#foco').innerHTML = `
    <div class="numeros">
      <div class="num"><b>${fmtPct(v.pr)}</b><span>Raquel Lyra</span></div>
      <div class="num"><b>${fmtPct(v.pa)}</b><span>${ADV[el]}</span></div>
      ${extra}
      <div class="num"><b style="font-size:17px">${v.vn}</b><span>mais votado</span></div>
    </div>
    <div class="barra" aria-hidden="true"><i style="width:${v.pr}%;background:${corCat('R')}"></i><i style="width:${v.pa}%;background:${corAdv}"></i><i style="width:${outros}%;background:${cor('--empate')}"></i></div>
    ${estado.foco && NIVEIS[estado.nivel] === 'municipio' ? prefeitoHTML(estado.foco) : ''}
    <p class="meta">${ELEICAO_NOME[el]} · percentuais sobre ${estado.denom === 'w' ? 'votos válidos' : 'votos totais'}${estado.foco ? ' · <button class="botao-texto" id="limpa-foco">voltar ao estado</button>' : ''}</p>`;
  const b = $('#limpa-foco');
  if (b) b.onclick = () => { estado.foco = null; atualizaFoco(); destacaFoco(); };
}
function destacaFoco() {
  mapa.setFilter('foco', ['==', ['get', 'id'], estado.foco && NIVEIS[estado.nivel] !== 'secao' ? String(estado.foco) : '']);
}

/* ---------------------------------------------------------------- tabela (mesmos números, acessível) */
let ordem = { col: 'n', desc: true };
function tabela() {
  const nivel = NIVEIS[estado.nivel];
  let ids = Object.keys(registroAtual);
  if (['secao', 'local'].includes(nivel)) {   // nos níveis finos, só o que está na tela
    const b = mapa.getBounds();
    const visiveis = new Set(mapa.querySourceFeatures('pontos').filter((f) => b.contains(f.geometry.coordinates)).map((f) => f.properties.id));
    ids = ids.filter((i) => visiveis.has(i));
  }
  const meta = dados.agregados.municipios_meta;
  const linhas = ids.map((id) => ({ id, nome: (titulos[id] || [id])[0], ...valores(registroAtual[id], estado.eleicao),
    pref: nivel === 'municipio' ? ({ R: 'Raquel', J: 'João', N: '—' }[meta[id]?.alianca] || '') : null })).filter((r) => r.t);
  const col = ordem.col;
  linhas.sort((a, b) => (ordem.desc ? -1 : 1) * ((a[col] ?? -1e9) > (b[col] ?? -1e9) ? 1 : (a[col] ?? -1e9) < (b[col] ?? -1e9) ? -1 : 0));
  const lim = linhas.slice(0, 400);
  const colVar = estado.leitura === 'var';
  $('#tabela-titulo').textContent = `${NIVEL_NOME[estado.nivel]} · ${ELEICAO_NOME[estado.eleicao]}${lim.length < linhas.length ? ` · ${lim.length} de ${linhas.length}` : ''}`;
  $('#tabela').innerHTML = `<thead><tr><th data-c="nome">Unidade</th><th data-c="n">${estado.denom === 'w' ? 'Válidos' : 'Votos'}</th><th data-c="pr">Raquel</th><th data-c="pa">${ADV[estado.eleicao].split(' ')[0]}</th>${colVar ? `<th data-c="${estado.base}">Variação</th>` : '<th data-c="vn">Mais votado</th>'}${nivel === 'municipio' ? '<th data-c="pref">Prefeito com</th>' : ''}</tr></thead>
    <tbody>${lim.map((r) => `<tr><td>${r.nome}</td><td>${fmtInt.format(r.n)}</td><td>${fmtPct(r.pr)}</td><td>${fmtPct(r.pa)}</td><td>${colVar ? fmtPp(r[estado.base]) : r.vn}</td>${nivel === 'municipio' ? `<td>${r.pref}</td>` : ''}</tr>`).join('')}</tbody>`;
  $('#tabela').querySelectorAll('th').forEach((th) => th.onclick = () => {
    ordem = { col: th.dataset.c, desc: ordem.col === th.dataset.c ? !ordem.desc : true }; tabela();
  });
}

/* ---------------------------------------------------------------- controles */
function marca(grupo, valor, attr) {
  document.querySelectorAll(`${grupo} button`).forEach((b) => b.setAttribute(attr, String(b.dataset.v === valor)));
}
function sincroniza() {
  marca('#eleicao', estado.eleicao, 'aria-checked');
  marca('#leitura', estado.leitura, 'aria-selected');
  marca('#var-base', estado.base, 'aria-checked');
  marca('#base-pct', estado.denom, 'aria-checked');
  $('#var-base').hidden = estado.leitura !== 'var';
  document.querySelectorAll('#eleicao button').forEach((b) => {
    b.disabled = estado.leitura === 'var' ? b.dataset.v !== '2026T1' : estado.leitura === 'dif' && b.dataset.v === '2022T2';
  });
  const aviso = $('#aviso-leitura');
  aviso.hidden = !['var', 'dif', 'pref'].includes(estado.leitura);
  aviso.textContent = estado.leitura === 'pref'
    ? 'Lado declarado pelos prefeitos em 2026 (lista do Jamildo.com). Mostra só município; a eleição escolhida vale para a dica e o painel. Prefeito aliado e voto andam juntos, mas isso não mostra causa.'
    : estado.leitura === 'var'
    ? 'Variação só para 2026, onde a unidade existe nas duas eleições. As eleições são de natureza diferente (turno, posição de Raquel, adversário), então a variação descreve, não mede ganho ou perda.'
    : 'Bloco PSB: Danilo Cabral em 2022 (1º turno) e João Campos em 2026. O 2º turno de 2022 não entra.';
  $('#nivel').disabled = estado.leitura === 'pref';
  $('#nivel').value = estado.nivel;
  $('#nivel-nome').textContent = NIVEL_NOME[estado.nivel];
}
function liga() {
  $('#eleicao').addEventListener('click', (e) => { const v = e.target.closest('button')?.dataset.v; if (!v || e.target.disabled) return; estado.eleicao = v; sincroniza(); desenha(); });
  $('#leitura').addEventListener('click', (e) => {
    const v = e.target.closest('button')?.dataset.v; if (!v) return;
    estado.leitura = v;
    if (v === 'var') estado.eleicao = '2026T1';
    if (v === 'pref') { estado.nivel = 3; estado.foco = null; }
    if (v === 'dif' && estado.eleicao === '2022T2') estado.eleicao = '2026T1';
    sincroniza(); desenha();
  });
  $('#base-pct').addEventListener('click', (e) => { const v = e.target.closest('button')?.dataset.v; if (!v) return; estado.denom = v; sincroniza(); desenha(); });
  $('#var-base').addEventListener('click', (e) => { const v = e.target.closest('button')?.dataset.v; if (!v) return; estado.base = v; sincroniza(); desenha(); });
  $('#nivel').addEventListener('input', (e) => { estado.nivel = +e.target.value; estado.foco = null; sincroniza(); desenha(); });
  $('#ver-noronha').onclick = () => mapa.flyTo({ center: [-32.42, -3.855], zoom: 11.5 });
  $('#ver-estado').onclick = () => mapa.fitBounds([[-41.4, -9.55], [-34.75, -7.25]], { padding: 24 });
  $('#ver-tabela').onclick = () => { const a = $('#tabela-area'); a.hidden = !a.hidden; $('#ver-tabela').setAttribute('aria-expanded', String(!a.hidden)); if (!a.hidden) tabela(); };
  $('#fechar-tabela').onclick = () => { $('#tabela-area').hidden = true; $('#ver-tabela').setAttribute('aria-expanded', 'false'); };
  mapa.on('moveend', () => { if (!$('#tabela-area').hidden && ['secao', 'local'].includes(NIVEIS[estado.nivel])) tabela(); });
  const meta = dados.agregados.municipios_meta;
  const porNome = Object.fromEntries(Object.entries(meta).map(([cd, m]) => [m.nome, cd]));
  $('#lista-municipios').innerHTML = Object.keys(porNome).sort((a, b) => a.localeCompare(b, 'pt')).map((n) => `<option value="${n}">`).join('');
  $('#busca').addEventListener('change', (e) => {
    const cd = porNome[e.target.value]; if (!cd) return;
    const f = dados.municipiosGeo.features.find((x) => x.properties.id === cd);
    const [x0, y0, x1, y1] = turf.bbox(f);
    mapa.fitBounds([[x0, y0], [x1, y1]], { padding: 40, maxZoom: 12 });
    if (estado.nivel === 3) { estado.foco = cd; atualizaFoco(); destacaFoco(); }
  });
}

/* ---------------------------------------------------------------- início */
const carga = Promise.all([json('data/agregados.json'), json('data/municipios.geojson')]);
// o painel não espera o mapa de fundo: mostra os números do estado assim que os dados chegam
carga.then(([ag, geo]) => { dados.agregados = ag; dados.municipiosGeo = geo; sincroniza(); legenda(); atualizaFoco(); })
  .catch((err) => {
    $('#foco').innerHTML = `<p class="meta">Não foi possível carregar os dados (${err.message}). Abra o site por um servidor (GitHub Pages ou <code>python -m http.server</code>), não direto do arquivo.</p>`;
  });
mapa.on('load', async () => {
  try { await carga; camadas(); liga(); await desenha(); } catch (err) { /* mensagem já mostrada no painel */ }
});
