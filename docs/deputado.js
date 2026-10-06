/* Mapa eleitoral de Pernambuco: onde cada deputado eleito em 2026 teve seus votos, sozinho ou somado
   com os eleitos do mesmo partido ou da mesma federação.
   Dados gerados por src/exporta_mapa.py: agregados.json (válidos por cargo e lado dos eleitos),
   pontos_<nível>_dep.json (posições e válidos por seção, local e zona) e deputados/<cargo>_<número>.json
   (votos do eleito por unidade; seção, local e zona na ordem das linhas dos pontos). */
'use strict';

const NIVEIS = ['secao', 'local', 'zona', 'municipio', 'rd', 'meso', 'estado'];
const NIVEL_NOME = ['Seção', 'Local de votação', 'Zona eleitoral', 'Município', 'Região de Desenvolvimento', 'Mesorregião', 'Estado'];
const CARGO_NOME = { DE2026: 'Deputado estadual', DF2026: 'Deputado federal' };
const LADO_NOME = { R: 'com Raquel Lyra', J: 'com João Campos', O: 'sem lado declarado' };
const GRUPO_NOME = { R: 'Bloco Raquel', J: 'Bloco João', O: 'Outros / sem lado' };
const COLIG_NOME = { R: 'Coligação de Raquel', J: 'Coligação de João', O: 'Fora das duas coligações' };
const MODO_NOME = { eleito: 'Eleito', partido: 'Partido', federacao: 'Federação' };

/* rampas pelo lado do eleito: roxo (Raquel), amarelo (João), cinza (sem lado) */
const RAMPA = {
  R: ['#efecf8', '#dcd5f1', '#c3b8e6', '#a697d9', '#8875ca', '#6b55b8', '#5240a3', '#3b2c85'],
  J: ['#fdf4dc', '#fbe6b0', '#f7d27a', '#f0bb45', '#e3a31c', '#c98a00', '#a36f00', '#7a5200'],
  O: ['#f0f1f3', '#dcdee2', '#c3c6cc', '#a7abb3', '#8b8f97', '#70747c', '#565a62', '#3d4047'],
};
const LIMITES = { pct: [0.5, 1, 2, 5, 10, 20, 35], peso: [0.1, 0.25, 0.5, 1, 2, 5, 10] };

const estado = { cargo: 'DE2026', modo: 'eleito', sel: null, leitura: 'pct', nivel: 3, foco: null };
const dados = { agregados: null, municipiosGeo: null, pontos: {}, poligonos: {}, eleito: {} };
const $ = (s) => document.querySelector(s);
const fmtInt = new Intl.NumberFormat('pt-BR');
const fmtPct = (x, d = 1) => (x == null || Number.isNaN(x) ? '—' : x.toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) + '%');
const cor = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const título = (x) => x.toLowerCase().replace(/(^|[\s(])(\p{L})/gu, (m, a, b) => a + b.toUpperCase())
  .replace(/ (De|Da|Do|Dos|Das|E) /g, (m) => m.toLowerCase()).replace(/\b(Pt|Pl|Psb|Psd)\b/g, (m) => m.toUpperCase());

/* eleitos do cargo: [{nr, nome, partido, bloco, votos, fonte, federacao, blocoPartido}] por votos */
const eleitos = (cargo) => Object.entries(dados.agregados.candidatos[cargo]).filter(([, c]) => c[3])
  .map(([nr, c]) => ({ nr, nome: título(c[0]), partido: c[1], bloco: c[2], votos: c[4], fonte: c[5],
    federacao: c[6] ? título(c[6]).replace(/^Federação /, '').replace(/ - .*$/, '').replace(/\b(Psol|Psdb)\b/g, (m) => m.toUpperCase()) : null, blocoPartido: c[7] }))
  .sort((a, b) => b.votos - a.votos);

/* grupos do modo atual: um eleito, os eleitos de um partido ou os de uma federação.
   Cor: lado do eleito; para partido e federação, lado do partido na coligação de governador (TSE). */
function grupos(cargo, modo) {
  const l = eleitos(cargo);
  if (modo === 'eleito') return l.map((e) => ({ id: e.nr, nome: e.nome, rotulo: `${e.nome} (${e.partido})`, bloco: e.bloco, membros: [e], votos: e.votos }));
  const chave = modo === 'partido' ? (e) => e.partido : (e) => e.federacao;
  const por = {};
  for (const e of l) if (chave(e)) (por[chave(e)] ||= []).push(e);
  return Object.entries(por).map(([id, m]) => ({ id, nome: modo === 'partido' ? id : `Federação ${id}`, rotulo: modo === 'partido' ? id : `Federação ${id}`,
    bloco: m[0].blocoPartido, membros: m, votos: m.reduce((a, e) => a + e.votos, 0) })).sort((a, b) => b.votos - a.votos);
}
const grupoAtual = () => grupos(estado.cargo, estado.modo).find((g) => g.id === estado.sel);
const deQuem = (g) => (estado.modo === 'eleito' ? g.nome : `eleitos ${estado.modo === 'partido' ? 'do' : 'da'} ${g.nome}`);

function classe(valor, votos) {
  if (!votos) return cor('--sem-dado');   // sem voto no lugar
  const lim = LIMITES[estado.leitura];
  let i = lim.findIndex((l) => valor < l);
  if (i === -1) i = lim.length;
  return RAMPA[grupoAtual().bloco][i];
}

/* ---------------------------------------------------------------- carga */
async function json(url) { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }
async function pontos(nivel) {
  if (!dados.pontos[nivel]) {
    $('#carregando').hidden = nivel !== 'secao';
    dados.pontos[nivel] = await json(`data/pontos_${nivel}_dep.json`);
    $('#carregando').hidden = true;
  }
  return dados.pontos[nivel];
}
async function votosEleito(cargo, nr) {
  const k = `${cargo}_${nr}`;
  if (!dados.eleito[k]) dados.eleito[k] = await json(`data/deputados/${k}.json`);
  return dados.eleito[k];
}
/* votos do grupo: soma dos arquivos dos eleitos (listas na mesma ordem; dicionários por id) */
async function votosGrupo(g) {
  const vs = await Promise.all(g.membros.map((e) => votosEleito(estado.cargo, e.nr)));
  if (vs.length === 1) return vs[0];
  const soma = {};
  for (const nivel of NIVEIS) {
    if (Array.isArray(vs[0][nivel])) soma[nivel] = vs[0][nivel].map((_, i) => vs.reduce((a, v) => a + v[nivel][i], 0));
    else { soma[nivel] = {}; for (const v of vs) for (const [k, x] of Object.entries(v[nivel])) soma[nivel][k] = (soma[nivel][k] || 0) + x; }
  }
  return soma;
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
const mapa = new maplibregl.Map({
  container: 'mapa',
  style: 'https://tiles.openfreemap.org/styles/positron',
  bounds: [[-41.4, -9.55], [-34.75, -7.25]],
  fitBoundsOptions: { padding: 24 },
  attributionControl: { compact: true },
  dragRotate: false, pitchWithRotate: false,
});
mapa.touchZoomRotate.disableRotation();
mapa.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10, maxWidth: '280px' });

function camadas() {
  const antes = mapa.getStyle().layers.find((l) => l.type === 'symbol')?.id;
  mapa.addSource('area', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, promoteId: 'id' });
  mapa.addSource('contorno', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  mapa.addSource('pontos', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  mapa.addLayer({ id: 'area', type: 'fill', source: 'area', paint: { 'fill-color': ['get', 'c'], 'fill-opacity': 0.9 } }, antes);
  mapa.addLayer({ id: 'area-linha', type: 'line', source: 'area', paint: {
    'line-color': 'rgba(255,255,255,0.95)', 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.7, 9, 1.2, 12, 1.8] } }, antes);
  mapa.addLayer({ id: 'contorno', type: 'line', source: 'contorno', paint: {
    'line-color': 'rgba(13,31,60,0.32)', 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.6, 12, 1.2] } }, antes);
  mapa.addSource('limite', { type: 'geojson', data: { type: 'FeatureCollection', features: poligonos('estado') } });
  mapa.addLayer({ id: 'limite', type: 'line', source: 'limite', paint: {
    'line-color': '#0c2856', 'line-opacity': 0.85, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 1.4, 10, 2.2] } }, antes);
  mapa.addLayer({ id: 'pontos', type: 'circle', source: 'pontos', paint: {
    'circle-color': ['get', 'c'],
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, ['*', ['get', 's'], 0.55], 10, ['*', ['get', 's'], 1.3], 14, ['*', ['get', 's'], 3.2]],
    'circle-stroke-color': 'rgba(13,31,60,0.45)', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 6, 0.3, 12, 0.8] } }, antes);
  mapa.addLayer({ id: 'foco', type: 'line', source: 'area', filter: ['==', ['get', 'id'], ''], paint: { 'line-color': '#0c2856', 'line-width': 2 } }, antes);
  for (const camada of ['area', 'pontos']) {
    mapa.on('mousemove', camada, (e) => { mapa.getCanvas().style.cursor = 'pointer'; mostraPopup(e.features[0], e.lngLat); });
    mapa.on('mouseleave', camada, () => { mapa.getCanvas().style.cursor = ''; popup.remove(); });
    mapa.on('click', camada, (e) => { estado.foco = e.features[0].properties.id; atualizaFoco(); destacaFoco(); });
  }
}

/* ---------------------------------------------------------------- desenho */
let registroAtual = {};   // id -> {votos, w (válidos do cargo), rq (Raquel governadora, % válidos)}
let titulos = {};
let totalEleito = 0;

async function desenha() {
  const nivel = NIVEIS[estado.nivel], cargo = estado.cargo, nr = `${estado.modo}|${estado.sel}`;
  const ag = dados.agregados;
  const ve = await votosGrupo(grupoAtual());
  const mudou = () => cargo !== estado.cargo || nr !== `${estado.modo}|${estado.sel}`;
  if (mudou()) return;   // o usuário trocou de escolha durante a carga
  totalEleito = ve.estado.Pernambuco;
  registroAtual = {}; titulos = {}; popup.remove();
  const reg = (votos, w, rq) => ({ votos, w, pct: w ? (votos / w) * 100 : null, peso: (votos / totalEleito) * 100, rq });
  if (['municipio', 'rd', 'meso', 'estado'].includes(nivel)) {
    const fc = poligonos(nivel).map((f) => {
      const id = f.properties.id;
      const a = ag[nivel][id];
      const g = a['2026T1'];
      const r = reg(ve[nivel][id] || 0, a[cargo][5], g[5] ? (g[1] / g[5]) * 100 : null);
      registroAtual[id] = r;
      titulos[id] = [f.properties.nome, nivel === 'municipio' ? ag.municipios_meta[id].rd : NIVEL_NOME[estado.nivel]];
      return { ...f, properties: { ...f.properties, c: classe(r[estado.leitura], r.votos) } };
    });
    mapa.getSource('area').setData({ type: 'FeatureCollection', features: fc });
    const fator = nivel === 'municipio' ? 1 : 2;
    mapa.setPaintProperty('area-linha', 'line-width', ['interpolate', ['linear'], ['zoom'], 6, 0.7 * fator, 9, 1.2 * fator, 12, 1.8 * fator]);
    mapa.getSource('pontos').setData({ type: 'FeatureCollection', features: [] });
    mapa.getSource('contorno').setData({ type: 'FeatureCollection', features: [] });
  } else {
    const p = await pontos(nivel);
    if (NIVEIS[estado.nivel] !== nivel || mudou()) return;
    const bloco = p[cargo];
    const meta = ag.municipios_meta;
    const base = nivel === 'secao' ? 2.2 : nivel === 'local' ? 0.16 : 0.035;
    const feats = bloco.linhas.map((l, i) => {
      const [x, y, iNome, iSub, cd, id, t, rq, , , , , , w, , , , gv] = l;
      // Raquel governadora (% válidos) = diferença governadora − bloco + % do bloco
      const r = reg(ve[nivel][i], w, gv == null || !w ? null : gv + (rq / w) * 100);
      registroAtual[id] = r;
      const titulo = nivel === 'secao' ? `Seção ${id.split('-')[1]} · Zona ${id.split('-')[0]}` : bloco.textos[iNome];
      titulos[id] = [titulo, `${bloco.textos[iSub]}${meta[cd] ? ' · ' + meta[cd].nome : ''}`];
      const s = nivel === 'secao' ? base : base * Math.sqrt(t);
      return { type: 'Feature', geometry: { type: 'Point', coordinates: [x, y] }, properties: { id, c: classe(r[estado.leitura], r.votos), s } };
    });
    feats.sort((f, g) => g.properties.s - f.properties.s);
    mapa.getSource('pontos').setData({ type: 'FeatureCollection', features: feats });
    mapa.getSource('area').setData({ type: 'FeatureCollection', features: [] });
    mapa.getSource('contorno').setData({ type: 'FeatureCollection', features: poligonos('municipio') });
  }
  ficha(ve); legenda(); atualizaFoco(); destacaFoco(); topMunicipios(ve);
  if (!$('#tabela-area').hidden) tabela();
}

/* ---------------------------------------------------------------- textos */
function linkFonte(f) {
  if (!f) return 'pela coligação de governador do partido (TSE)';
  const url = (f.match(/https?:\/\/[^\s);]+/) || [''])[0];
  const texto = f.replace(/:?\s*https?:\/\/[^\s);]+/, '').replace(/"/g, '&quot;');
  return `<span title="${texto}">pelo apoio público${url ? ` (<a href="${url}" target="_blank" rel="noopener">fonte</a>)` : ''}</span>`;
}
function ficha(ve) {
  const g = grupoAtual();
  const w = dados.agregados.estado.Pernambuco[estado.cargo][5];
  if (estado.modo !== 'eleito') {
    const n = g.membros.reduce((a, e) => (a[e.bloco] = (a[e.bloco] || 0) + 1, a), {});
    const lados = ['R', 'J', 'O'].filter((b) => n[b]).map((b) => `${n[b]} ${LADO_NOME[b]}`).join(', ');
    $('#ficha').innerHTML = `
      <p class="ficha-nome">${g.nome}</p>
      <p class="ficha-lado"><i style="background:${RAMPA[g.bloco][6]}"></i>${COLIG_NOME[g.bloco]} (cor do mapa)</p>
      <p class="meta">${g.membros.length} ${g.membros.length === 1 ? 'eleito' : 'eleitos'}: ${lados}.</p>
      <div class="ficha-numeros">
        <div class="num"><b>${fmtInt.format(ve.estado.Pernambuco)}</b><span>votos dos eleitos somados</span></div>
        <div class="num"><b>${fmtPct((ve.estado.Pernambuco / w) * 100, 2)}</b><span>dos votos válidos no estado</span></div>
      </div>
      <ol class="top-lista">${g.membros.map((e) => `<li><button data-nr="${e.nr}" title="Ver só ${e.nome}"><i class="bola" style="background:${RAMPA[e.bloco][6]}"></i>${e.nome}${estado.modo === 'federacao' ? ` (${e.partido})` : ''}</button>
        <span>${fmtInt.format(e.votos)}</span><span>${LADO_NOME[e.bloco].replace('com ', '').replace(' declarado', '')}</span></li>`).join('')}</ol>`;
    $('#ficha').querySelectorAll('button[data-nr]').forEach((b) => b.onclick = () => {
      estado.modo = 'eleito'; estado.sel = b.dataset.nr; opcoes(); sincroniza(); desenha();
    });
    return;
  }
  const e = g.membros[0];
  const lista = eleitos(estado.cargo);
  const posicao = lista.findIndex((x) => x.nr === e.nr) + 1;
  $('#ficha').innerHTML = `
    <p class="ficha-nome">${e.nome}</p>
    <p class="ficha-lado"><i style="background:${RAMPA[e.bloco][6]}"></i>${e.partido} · ${LADO_NOME[e.bloco]}</p>
    <p class="meta">Lado ${linkFonte(e.fonte)}.</p>
    <div class="ficha-numeros">
      <div class="num"><b>${fmtInt.format(ve.estado.Pernambuco)}</b><span>votos · ${posicao}º entre os ${lista.length} eleitos</span></div>
      <div class="num"><b>${fmtPct((ve.estado.Pernambuco / w) * 100, 2)}</b><span>dos votos válidos no estado</span></div>
    </div>`;
}
function legenda() {
  const e = grupoAtual();
  const lim = LIMITES[estado.leitura];
  const fmt = (x) => x.toLocaleString('pt-BR');
  const rotulos = RAMPA[e.bloco].map((_, i) => (i === 0 ? '<' + fmt(lim[0]) : i === lim.length ? fmt(lim[i - 1]) + '+' : fmt(lim[i - 1])));
  $('#legenda-titulo').textContent = (estado.leitura === 'pct' ? '% dos votos válidos no lugar' : `% da votação ${estado.modo === 'eleito' ? 'do eleito' : 'dos eleitos'}`) + ` · ${e.nome}`;
  $('#legenda').innerHTML = `<div class="escala">${RAMPA[e.bloco].map((c) => `<span style="background:${c}"></span>`).join('')}</div>
    <div class="escala escala-rotulos">${rotulos.map((r) => `<em>${r}</em>`).join('')}</div>
    <div class="escala-pontas"><span>menos votos</span><span>mais votos (%)</span></div>
    <div class="cats"><div class="cat"><i style="background:${cor('--sem-dado')}"></i>Nenhum voto ${estado.modo === 'eleito' ? 'do eleito' : 'dos eleitos'}</div></div>`;
  const quem = estado.modo === 'eleito' ? 'do eleito' : `dos ${deQuem(e)}, somados,`;
  const corTxt = estado.modo === 'eleito' ? `Cor pelo lado dele: ${LADO_NOME[e.bloco]}.`
    : `Cor pelo lado do partido na coligação de governador: ${COLIG_NOME[e.bloco].replace(/^./, (c) => c.toLowerCase())}.`;
  $('#aviso-leitura').textContent = estado.leitura === 'pct'
    ? `Votos ${quem} sobre os votos válidos para ${CARGO_NOME[estado.cargo].toLowerCase()} em cada lugar. ${corTxt}`
    : `Quanto da votação total ${quem.replace(', somados,', '')} saiu de cada lugar. Mostra a base eleitoral. ${corTxt}`;
}
function linhaPop(nome, valor) { return `<div class="pop-linha"><span>${nome}</span><span>${valor}</span></div>`; }
function mostraPopup(f, lngLat) {
  const id = f.properties.id;
  const r = registroAtual[id];
  const [t, sub] = titulos[id] || [id, ''];
  const e = grupoAtual();
  const corpo = r ? linhaPop(`Votos ${estado.modo === 'eleito' ? 'de ' + e.nome : 'dos eleitos'}`, fmtInt.format(r.votos)) + linhaPop('% dos válidos no lugar', fmtPct(r.pct))
    + linhaPop(`% da votação ${estado.modo === 'eleito' ? 'do eleito' : 'dos eleitos'}`, fmtPct(r.peso, 2)) + linhaPop('Raquel governadora (válidos)', fmtPct(r.rq)) : '';
  popup.setLngLat(lngLat).setHTML(`<p class="pop-titulo">${t}</p><p class="pop-sub">${sub}</p>${corpo}`).addTo(mapa);
}
function atualizaFoco() {
  const id = estado.foco && registroAtual[estado.foco] ? estado.foco : null;
  const r = id ? registroAtual[id] : null;
  const e = grupoAtual();
  const de = estado.modo === 'eleito' ? 'do eleito' : 'dos eleitos';
  $('#foco-rotulo').textContent = id ? titulos[id][0] : 'Clique num lugar do mapa';
  if (!r) { $('#foco').innerHTML = `<p class="meta">Clique num município, seção ou região para ver os votos ${estado.modo === 'eleito' ? 'de ' + e.nome : 'dos ' + deQuem(e)} ali.</p>`; return; }
  $('#foco').innerHTML = `<div class="numeros">
      <div class="num"><b>${fmtInt.format(r.votos)}</b><span>votos ${de}</span></div>
      <div class="num"><b>${fmtPct(r.pct)}</b><span>dos válidos no lugar</span></div>
      <div class="num"><b>${fmtPct(r.peso, 2)}</b><span>da votação ${de}</span></div>
      <div class="num"><b>${fmtPct(r.rq)}</b><span>Raquel governadora (válidos)</span></div>
    </div>
    <p class="meta">${fmtInt.format(r.w)} votos válidos para ${CARGO_NOME[estado.cargo].toLowerCase()} · <button class="botao-texto" id="limpa-foco">limpar</button></p>`;
  $('#limpa-foco').onclick = () => { estado.foco = null; atualizaFoco(); destacaFoco(); };
}
function destacaFoco() {
  mapa.setFilter('foco', ['==', ['get', 'id'], estado.foco && NIVEIS[estado.nivel] !== 'secao' ? String(estado.foco) : '']);
}
function topMunicipios(ve) {
  const ag = dados.agregados;
  const l = Object.entries(ve.municipio).sort((a, b) => b[1] - a[1]).slice(0, 8);
  $('#top').innerHTML = l.map(([cd, v]) => `<li><button data-cd="${cd}">${ag.municipios_meta[cd].nome}</button>
    <span>${fmtInt.format(v)}</span><span>${fmtPct((v / ag.municipio[cd][estado.cargo][5]) * 100)}</span></li>`).join('');
  $('#top').querySelectorAll('button').forEach((b) => b.onclick = () => vaiPara(b.dataset.cd));
}

/* ---------------------------------------------------------------- tabela */
let ordem = { col: 'votos', desc: true };
function tabela() {
  const nivel = NIVEIS[estado.nivel];
  let ids = Object.keys(registroAtual);
  if (['secao', 'local'].includes(nivel)) {
    const b = mapa.getBounds();
    const visiveis = new Set(mapa.querySourceFeatures('pontos').filter((f) => b.contains(f.geometry.coordinates)).map((f) => f.properties.id));
    ids = ids.filter((i) => visiveis.has(i));
  }
  const linhas = ids.map((id) => ({ id, nome: (titulos[id] || [id])[0], ...registroAtual[id] }));
  const col = ordem.col;
  linhas.sort((a, b) => (ordem.desc ? -1 : 1) * ((a[col] ?? -1e9) > (b[col] ?? -1e9) ? 1 : (a[col] ?? -1e9) < (b[col] ?? -1e9) ? -1 : 0));
  const lim = linhas.slice(0, 400);
  $('#tabela-titulo').textContent = `${grupoAtual().nome} · ${NIVEL_NOME[estado.nivel]}${lim.length < linhas.length ? ` · ${lim.length} de ${linhas.length}` : ''}`;
  $('#tabela').innerHTML = `<thead><tr><th data-c="nome">Unidade</th><th data-c="votos">Votos</th><th data-c="pct">% dos válidos</th><th data-c="peso">% da votação</th><th data-c="rq">Raquel gov.</th></tr></thead>
    <tbody>${lim.map((r) => `<tr><td>${r.nome}</td><td>${fmtInt.format(r.votos)}</td><td>${fmtPct(r.pct)}</td><td>${fmtPct(r.peso, 2)}</td><td>${fmtPct(r.rq)}</td></tr>`).join('')}</tbody>`;
  $('#tabela').querySelectorAll('th').forEach((th) => th.onclick = () => {
    ordem = { col: th.dataset.c, desc: ordem.col === th.dataset.c ? !ordem.desc : true }; tabela();
  });
}

/* ---------------------------------------------------------------- controles */
function marca(grupo, valor, attr) {
  document.querySelectorAll(`${grupo} button`).forEach((b) => b.setAttribute(attr, String(b.dataset.v === valor)));
}
function opcoes() {
  const l = grupos(estado.cargo, estado.modo);
  const nomes = estado.modo === 'eleito' ? GRUPO_NOME : COLIG_NOME;
  const conta = (g) => (estado.modo === 'eleito' ? '' : ` · ${g.membros.length} ${g.membros.length === 1 ? 'eleito' : 'eleitos'}`);
  $('#deputado').innerHTML = ['R', 'J', 'O'].map((b) => {
    const gs = l.filter((g) => g.bloco === b);
    return gs.length ? `<optgroup label="${nomes[b]} (${gs.length})">${gs.map((g) => `<option value="${g.id}">${g.rotulo}${conta(g)} · ${fmtInt.format(g.votos)}</option>`).join('')}</optgroup>` : '';
  }).join('');
  if (!l.some((g) => g.id === estado.sel)) estado.sel = l[0].id;
  $('#deputado').value = estado.sel;
  $('#rotulo-escolha').textContent = MODO_NOME[estado.modo];
}
function sincroniza() {
  marca('#cargo', estado.cargo, 'aria-checked');
  marca('#modo', estado.modo, 'aria-checked');
  marca('#leitura', estado.leitura, 'aria-selected');
  $('#nivel').value = estado.nivel;
  $('#nivel-nome').textContent = NIVEL_NOME[estado.nivel];
  // link direto: #DE2026-13000 (eleito), #DE2026-partido-PT, #DE2026-federacao-PSOL%20Rede
  history.replaceState(null, '', `#${estado.cargo}-${estado.modo === 'eleito' ? '' : estado.modo + '-'}${encodeURIComponent(estado.sel)}`);
}
function vaiPara(cd) {
  const f = dados.municipiosGeo.features.find((x) => x.properties.id === cd);
  const [x0, y0, x1, y1] = turf.bbox(f);
  mapa.fitBounds([[x0, y0], [x1, y1]], { padding: 40, maxZoom: 12 });
  if (estado.nivel === 3) { estado.foco = cd; atualizaFoco(); destacaFoco(); }
}
function liga() {
  $('#cargo').addEventListener('click', (e) => {
    const v = e.target.closest('button')?.dataset.v; if (!v || v === estado.cargo) return;
    estado.cargo = v; estado.sel = null; estado.foco = null; opcoes(); sincroniza(); desenha();
  });
  $('#modo').addEventListener('click', (e) => {
    const v = e.target.closest('button')?.dataset.v; if (!v || v === estado.modo) return;
    estado.modo = v; estado.sel = null; opcoes(); sincroniza(); desenha();
  });
  $('#deputado').addEventListener('change', (e) => { estado.sel = e.target.value; sincroniza(); desenha(); });
  $('#leitura').addEventListener('click', (e) => { const v = e.target.closest('button')?.dataset.v; if (!v) return; estado.leitura = v; sincroniza(); desenha(); });
  $('#nivel').addEventListener('input', (e) => { estado.nivel = +e.target.value; estado.foco = null; sincroniza(); desenha(); });
  $('#ver-noronha').onclick = () => mapa.flyTo({ center: [-32.42, -3.855], zoom: 11.5 });
  $('#ver-estado').onclick = () => mapa.fitBounds([[-41.4, -9.55], [-34.75, -7.25]], { padding: 24 });
  $('#ver-tabela').onclick = () => { const a = $('#tabela-area'); a.hidden = !a.hidden; $('#ver-tabela').setAttribute('aria-expanded', String(!a.hidden)); if (!a.hidden) tabela(); };
  $('#fechar-tabela').onclick = () => { $('#tabela-area').hidden = true; $('#ver-tabela').setAttribute('aria-expanded', 'false'); };
  mapa.on('moveend', () => { if (!$('#tabela-area').hidden && ['secao', 'local'].includes(NIVEIS[estado.nivel])) tabela(); });
  const meta = dados.agregados.municipios_meta;
  const porNome = Object.fromEntries(Object.entries(meta).map(([cd, m]) => [m.nome, cd]));
  $('#lista-municipios').innerHTML = Object.keys(porNome).sort((a, b) => a.localeCompare(b, 'pt')).map((n) => `<option value="${n}">`).join('');
  $('#busca').addEventListener('change', (e) => { const cd = porNome[e.target.value]; if (cd) vaiPara(cd); });
}

/* ---------------------------------------------------------------- início */
const carga = Promise.all([json('data/agregados.json'), json('data/municipios.geojson')]);
carga.then(([ag, geo]) => {
  dados.agregados = ag; dados.municipiosGeo = geo;
  const partes = location.hash.slice(1).split('-');   // #DE2026-13000 ou #DE2026-partido-PT
  if (CARGO_NOME[partes[0]]) {
    estado.cargo = partes[0];
    if (MODO_NOME[partes[1]] && partes.length > 2) { estado.modo = partes[1]; estado.sel = decodeURIComponent(partes.slice(2).join('-')); }
    else estado.sel = decodeURIComponent(partes.slice(1).join('-'));
  }
  opcoes(); sincroniza();
}).catch((err) => {
  $('#ficha').innerHTML = `<p class="meta">Não foi possível carregar os dados (${err.message}). Abra o site por um servidor (GitHub Pages ou <code>python -m http.server</code>), não direto do arquivo.</p>`;
});
mapa.on('load', async () => {
  try { await carga; camadas(); liga(); await desenha(); } catch (err) { /* mensagem já mostrada no painel */ }
});
