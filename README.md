# Mapa eleitoral de Pernambuco · governador 2022–2026

Mapa interativo e análise dos votos para governador de Pernambuco no 1º e no 2º turno de 2022 e no 1º turno de 2026, da seção eleitoral ao estado.

**Mapa:** _(link do GitHub Pages, quando o repositório for público)_
**Conclusões:** [`CONCLUSOES.md`](CONCLUSOES.md)

Projeto independente de Diego Abreu. Não é publicação do Governo de Pernambuco nem de campanha.

## O que o mapa mostra

- **Eleição:** 2022 (1º turno), 2022 (2º turno) e 2026.
- **Leitura:** % de Raquel Lyra; candidato mais votado; Raquel menos o bloco PSB (Danilo Cabral em 2022, João Campos em 2026); variação de Raquel entre 2022 e 2026; lado declarado pelos prefeitos em 2026 (Jamildo.com).
- **Nível**, numa barra deslizante: seção, local de votação, zona, município, Região de Desenvolvimento, mesorregião e estado.
- **Base:** votos totais ou votos válidos.
- Tabela com os mesmos números, modo escuro e versão para celular.

## Perguntas da análise

1. Onde Raquel Lyra cresceu ou caiu entre 2022 e 2026, e qual o perfil dessas áreas.
2. Se a aliança dos prefeitos se relaciona com o voto dela em 2026.
3. Se a economia se relaciona com o voto, por município.

Resumo: a mudança entre as eleições foi territorial, município a município, e não de perfil social. A aliança do prefeito é a variável mais associada ao voto de Raquel em 2026 (7 a 12 pontos, robusta a vários testes), mas a análise mostra associação, não causa. Indicadores econômicos municipais e repasses estaduais acompanham pouco ou nada. Detalhes, graus de confiança e limites em [`CONCLUSOES.md`](CONCLUSOES.md).

## Método

- **Base dos percentuais:** no mapa, votos totais (brancos e nulos no denominador) ou votos válidos, à escolha. Na análise, votos totais. Os votos válidos conferem com o resultado oficial nas três eleições (Raquel: 20,58%, 58,70% e 53,27%).
- **Seções e locais:** seção não tem contorno oficial; no mapa, cada seção é um ponto ao redor do seu local de votação (coordenadas do TSE). Zona é um ponto no centro dos seus locais. 425 seções de 2022 sem coordenada recuperaram a do cadastro de 2026; seções de voto em trânsito entram nos totais e não nos pontos.
- **Comparação entre eleições:** seções casadas por zona + seção (20.404 nas duas eleições; 1.456 mudaram de local e ficam marcadas). Como turno, adversário e posição de Raquel mudam, a variação descreve e não mede ganho ou perda.
- **Movimento de eleitorados:** regressão de Goodman com restrição por seção, abstenção como categoria, incerteza por reamostragem de municípios.
- **Aliança dos prefeitos:** lista do Jamildo.com (estado em 06/10/2026), única fonte pública encontrada com classificação por município. Ressalvas no [`CONCLUSOES.md`](CONCLUSOES.md).
- **Robustez da associação aliança × voto:** controles (voto de 2022, renda, região), erro agrupado por microrregião com wild cluster bootstrap, placebo com 2022 e descontinuidade em eleições municipais apertadas de 2024 (inconclusiva por falta de casos).
- **Economia:** PNAD Contínua (estado), Censo 2022 (renda por município), Bolsa Família (MDS), Novo CAGED (emprego formal, out/2025 a ago/2026) e transferências do estado declaradas pelos municípios (SICONFI).

## Fontes

| Dado | Fonte |
|---|---|
| Votação por seção, candidatos, locais de votação, comparecimento, perfil do eleitorado | [TSE, Portal de Dados Abertos](https://dadosabertos.tse.jus.br/) |
| Malha municipal, mesorregiões, Censo 2022, PNAD Contínua | [IBGE](https://www.ibge.gov.br/) (APIs de malhas, localidades e agregados) |
| Regiões de Desenvolvimento | [BDE/Condepe-Fidem](http://www.bde.pe.gov.br/) |
| Bolsa Família | MDS, API MI Social |
| Emprego formal | Novo CAGED, PDET/Ministério do Trabalho |
| Transferências do estado a municípios | SICONFI, Tesouro Nacional |
| Aliança dos prefeitos | [Jamildo.com](https://jamildo.com/) |
| Mapa base | © OpenStreetMap, OpenMapTiles, OpenFreeMap |

## Como reproduzir

Os dados brutos não estão no repositório (vários GB). Os scripts esperam esta estrutura, com as pastas de dados ao lado do projeto:

```
estudos-dados/
├── mapa-eleitoral-pe/        este repositório
├── dados-tse/                arquivos do TSE (2022, 2024, 2026)
├── dados-ibge/               malha, municípios, Censo, PNAD
├── dados-siconfi/            gerado por src/coleta_siconfi.py
├── dados-mds/                Bolsa Família (API MI Social)
└── dados-caged/              gerado por src/coleta_caged.py
```

Ordem: `limpeza.py` → `analise_p1.py` → `transferencia*.py` → `regressao_municipio.py` → `coleta_siconfi.py` → `placebo.py`, `robustez_cluster.py`, `descontinuidade_2024.py` → `bolsa_familia.py`, `coleta_caged.py`, `caged_voto.py` → `exporta_mapa.py`. A lista de alianças vem da planilha publicada que alimenta o mapa do Jamildo.com. O site mostra o lado de cada prefeito, com crédito; a planilha bruta não é redistribuída aqui.

Para ver o mapa localmente:

```
python -m http.server 8000 --directory site
```

## Identidade visual

Identidade própria, inspirada no manual de marca do Governo de Pernambuco (azul-marinho, tipografia de desenho DIN). Não usa logotipo, brasão, slogan nem elementos da marca. Raquel Lyra em roxo e João Campos em amarelo seguem as cores das campanhas; as cores foram validadas para leitura por pessoas com daltonismo.
