# Conclusões — governador de PE, 2022 x 2026

Escritas em 06/10/2026, depois de todas as análises. Os números saem dos scripts em `src/` (pasta `resultados/`, gerada ao rodar); o método está no `README.md`. Cada conclusão traz o grau de confiança e o motivo.

## Perguntas

1. Onde Raquel Lyra cresceu ou caiu entre 2022 e 2026, e qual o perfil dessas áreas.
2. Se a aliança dos prefeitos se relaciona com o voto dela em 2026.
3. Se a economia se relaciona com o voto, por município.

Resultado de referência (TSE, votos válidos): Raquel 53,27% e João Campos 44,82% em 2026, eleita no 1º turno.

## Conclusões

### 1. A mudança entre 2022 e 2026 foi territorial, não de perfil social
**Confiança alta.**

Saber o município de uma seção explica 81,8% da variação do voto de Raquel entre as seções. Somar escolaridade, idade e sexo do eleitorado leva a 82,1%. Dentro de um mesmo município, o perfil quase não diz nada. A aparente ligação com escolaridade e renda no estado vem da RMR, que concentra mais renda e escolaridade e foi onde Raquel teve o pior resultado relativo.

O que isso não diz: perfil e voto foram medidos por seção, não por pessoa (inferência ecológica).

### 2. A comparação direta com 2022 não mede ganho nem perda de Raquel
**Confiança alta (é um limite de desenho).**

De 53,7% (2022, 2º turno) para 47,5% (2026), em votos totais, mudaram ao mesmo tempo: o turno, a posição dela (oposição para governo), o adversário (Marília para João) e o campo do PSB (dividido para unido). A queda de 14 pontos na RMR, por exemplo, não separa perda de Raquel de força de João na sua base. Por isso os números brutos ficam como descrição.

### 3. O tabuleiro: Raquel manteve a maior parte do seu eleitorado e trouxe parte do de Marília; João herdou a maior parte do eleitorado de Marília e de Danilo
**Confiança moderada a baixa.**

Estimativa por seção (regressão de Goodman com restrição; faixa de 200 reamostragens por município). De cada 100 votos do 2º turno de 2022: os de Raquel foram cerca de 66 para ela e 26 para João; os de Marília, cerca de 32 para Raquel e 56 para João. Do 1º turno de 2022: os de Danilo (PSB) foram cerca de 39 para Raquel e 56 para João; os de Miguel, cerca de 53 para Raquel.

Por que moderada a baixa: o voto de 2022 explica só de 15% a 42% do voto de 2026 na seção, o modelo supõe o mesmo movimento em todo o estado, e é inferência ecológica.

### 4. A aliança do prefeito é, de longe, a variável mais associada ao voto de Raquel em 2026
**Associação: confiança alta. Efeito causal: não estabelecido.**

Municípios com prefeito aliado deram a Raquel de 7 a 12 pontos a mais, controlando o voto de 2022, a renda e a região. A associação resistiu a todos os testes feitos:
- dez especificações diferentes (com e sem peso pelos votos, com e sem efeito fixo de RD);
- erro agrupado por microrregião e wild cluster bootstrap (p ≤ 0,01 em todas as versões);
- placebo: a aliança de 2026 não se associa ao voto de Raquel em 2022, nem ao nível nem ao crescimento entre turnos. Os prefeitos não escolheram lado com base no desempenho dela em 2022.

O que fica em aberto: a descontinuidade com as eleições municipais apertadas de 2024 deu estimativas na mesma faixa (8 a 11 pontos), mas com poucos casos perto do corte e com 23 prefeitos que trocaram de lado depois de eleitos. Ela não tem dado suficiente para separar efeito de seleção. Também não dá para descartar que prefeitos tenham aderido onde Raquel ganhou força entre 2022 e 2026 (Novaes 2018), porque isso não aparece em dado de voto.

A mesma diferença aparece no movimento dos eleitorados: onde o prefeito é aliado de Raquel, cerca de 32 em cada 100 eleitores de Marília (2022) foram para ela em 2026; onde o prefeito é de João, cerca de 11.

### 5. Os repasses do governo chegaram a todos os municípios, mas não na mesma proporção
**Distribuição: confiança alta. Relação com o voto: fraca e instável.**

- Cobertura: praticamente todos os municípios receberam transferências não constitucionais do estado em todos os anos. Nesse sentido, "para todos" se confirma.
- Distribuição: em 2022 (governo anterior) aliados e não aliados recebiam o mesmo por habitante. Em 2024 e 2025, municípios de prefeito aliado receberam mais (mediana 1,5 e 1,65 vez; em 2025, 64,5% da população e 82,7% do dinheiro). Em 2026, até junho, a diferença diminui e deixa de ser distinguível do acaso.
- Voto: a associação das transferências com o voto de Raquel é de no máximo uns 3 pontos entre um município de repasse baixo e um de repasse alto, varia conforme o modelo e encolhe quando a aliança entra. Transferência e aliança andam juntas, mas os dados não dizem quem puxa quem.

### 6. A economia local não explica as diferenças de voto entre municípios
**Confiança alta para o que foi medido.**

Bolsa Família (nível e variação de 2022 para 2026), emprego formal no ano eleitoral (Novo CAGED) e renda per capita (Censo 2022) não mostram associação estável com o voto de Raquel por município.

O que isso não diz: a economia do estado melhorou entre 2022 e 2026 (PNAD: desemprego de 14,0% para 8,3%; renda domiciliar per capita +41% real de 2022 a 2025, contra +29% no Nordeste). Essa melhora é comum a todos os municípios, então não pode ser testada comparando um município com outro. A ausência de associação municipal não significa que a economia não pesou no resultado do estado.

## Síntese

O resultado de 2026 se organiza por território, município a município. Entre as variáveis medidas, a que mais acompanha essas diferenças é a aliança do prefeito, de forma robusta. Indicadores econômicos locais e repasses estaduais acompanham pouco ou nada. Os dados mostram associação; não provam que o prefeito causou o voto.

## Limites gerais

- Inferência ecológica em toda a análise de perfil e de movimento de eleitorados.
- Lista de alianças: só o Jamildo.com tem a lista por município; é a foto de 06/10/2026, sem categoria neutra, sem data de adesão; outras contagens divergem em até 5 municípios.
- Comparações entre eleições de natureza diferente (2º turno de 2022 x 1º turno de 2026).
- Transferências declaradas pelos próprios municípios ao Tesouro (SICONFI); qualidade da classificação varia.
- CAGED cobre só emprego com carteira; PNAD não desce a município.
- 184 municípios: pouco poder para desenhos quase-experimentais.

## O que fortaleceria as conclusões

- Pesquisa com eleitores (dado individual) que pergunte voto e avaliação do governo e do prefeito.
- A data em que cada prefeito declarou apoio, para ver se a adesão veio antes ou depois de repasses e de mudanças de popularidade.
- Série de repasses com o prefeito de cada ano (os de 2023–2024 eram outros em parte dos municípios).

## Referências de método usadas

- Rosen, Jiang, King e Tanner (2001), *Statistica Neerlandica* 55(2).
- Novaes (2018), *American Journal of Political Science* 62: 84–98.
- Ventura (2021), *Electoral Studies*, doi 10.1016/j.electstud.2020.102242.
- Feierherd (2020), *Journal of Politics*, doi 10.1086/705742.
- Cameron, Gelbach e Miller (2008), *Review of Economics and Statistics*, doi 10.1162/rest.90.3.414.
- Webb (2023), *Canadian Journal of Economics*, doi 10.1111/caje.12661.
