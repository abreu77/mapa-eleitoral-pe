# Conclusões — governador de PE, 2022 x 2026

Escritas em 06/10/2026, depois de todas as análises; atualizadas em 07/10/2026 (repasses de 2026 e inferência ecológica hierárquica). Os números saem dos scripts em `src/` (pasta `resultados/`, gerada ao rodar); o método está no `README.md`. Cada conclusão traz o grau de confiança e o motivo.

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
**Confiança moderada: dois métodos chegam a números parecidos, mas os dois são inferência ecológica.**

Estimativa por seção (regressão de Goodman com restrição; faixa de 200 reamostragens por município). De cada 100 votos do 2º turno de 2022: os de Raquel foram cerca de 66 para ela e 26 para João; os de Marília, cerca de 32 para Raquel e 56 para João. Do 1º turno de 2022: os de Danilo (PSB) foram cerca de 39 para Raquel e 56 para João; os de Miguel, cerca de 53 para Raquel.

Modelo hierárquico (Rosen et al. 2001), em que cada seção tem as suas próprias taxas, sobre o eleitorado apto (quem não votou em nenhum dos dois entra como "nenhum"): de cada 100 eleitores de Raquel no 2º turno de 2022, 64 votaram nela em 2026, 25 em João e 12 em nenhum dos dois; de cada 100 de Marília, 29 em Raquel, 65 em João e 6 em nenhum. Quatro cadeias independentes por grupo de municípios chegaram aos mesmos números (diferença máxima de 0,6 ponto), e três rodadas sucessivas, de 30, 90 e 270 mil iterações, mudaram menos de 1 ponto.

Por que não é alta: a regressão de Goodman explica só de 15% a 42% do voto de 2026 na seção e supõe o mesmo movimento em todo o estado; o modelo hierárquico corrige essa suposição, mas os dois estimam o comportamento médio de grupos a partir de dado agregado, não de pessoas.

### 4. A aliança do prefeito é, de longe, a variável mais associada ao voto de Raquel em 2026
**Associação: confiança alta. Efeito causal: não estabelecido.**

Municípios com prefeito aliado deram a Raquel de 7 a 12 pontos a mais, controlando o voto de 2022, a renda e a região. A associação resistiu a todos os testes feitos:
- dez especificações diferentes (com e sem peso pelos votos, com e sem efeito fixo de RD);
- erro agrupado por microrregião e wild cluster bootstrap (p ≤ 0,01 em todas as versões);
- placebo: a aliança de 2026 não se associa ao voto de Raquel em 2022, nem ao nível nem ao crescimento entre turnos. Os prefeitos não escolheram lado com base no desempenho dela em 2022.

O que fica em aberto: a descontinuidade com as eleições municipais apertadas de 2024 deu estimativas na mesma faixa (8 a 11 pontos), mas com poucos casos perto do corte e com 23 prefeitos que trocaram de lado depois de eleitos. Ela não tem dado suficiente para separar efeito de seleção. Também não dá para descartar que prefeitos tenham aderido onde Raquel ganhou força entre 2022 e 2026 (Novaes 2018), porque isso não aparece em dado de voto.

A mesma diferença aparece no movimento dos eleitorados. No modelo hierárquico, onde o prefeito é aliado de Raquel, 34 em cada 100 eleitores de Marília (2022) votaram nela em 2026; onde o prefeito é de João, 19 (diferença de 15 a 16 pontos). A regressão de Goodman dava 32 e 11. Raquel também manteve um pouco mais do próprio eleitorado onde o prefeito é aliado (66 contra 61 em cada 100).

### 5. Os repasses do governo chegaram a todos os municípios, mas não na mesma proporção, e cresceram muito em 2026
**Distribuição: confiança alta. Relação com o voto: fraca e instável.**

- Cobertura: praticamente todos os municípios receberam transferências não constitucionais do estado em todos os anos. Nesse sentido, "para todos" se confirma.
- Distribuição: em 2022 (governo anterior) aliados e não aliados recebiam o mesmo por habitante. Em 2024 e 2025, municípios de prefeito aliado receberam mais (mediana 1,5 e 1,65 vez; em 2025, 64,5% da população e 82,7% do dinheiro). Em 2026, até junho, a diferença diminui e deixa de ser distinguível do acaso.
- Ano eleitoral: comparando o mesmo período e a mesma medida (transferência de capital do estado, relatório bimestral RREO), o estado repassou R$ 806,6 milhões de janeiro a junho de 2026, contra R$ 43,6 milhões em 2024 e R$ 54,0 milhões em 2025. Até junho, o dinheiro chegou a quase todos e foi parecido entre aliados e oposição (mediana de R$ 152 e R$ 135 por habitante). Em julho e agosto de 2026, período em que a lei eleitoral proíbe transferência voluntária do estado aos municípios, salvo obra ou serviço já em andamento com cronograma e emergência ou calamidade (Lei 9.504/97, art. 73, VI, "a"), entraram R$ 175,3 milhões: R$ 171,0 milhões em municípios de prefeito aliado, que têm cerca de 64% da população. Receberam algo 88 de 130 municípios aliados e 14 de 36 de oposição. O padrão continua sem os 10 maiores recebedores. Julho e agosto de 2024 e 2025 também concentram em aliados, com valores menores. Os dados não separam obra em andamento (permitida) de transferência nova e não permitem dizer se houve irregularidade. A aliança usada é a dos prefeitos atuais; em 2024, parte dos municípios tinha outro prefeito.
- Voto: a associação das transferências com o voto de Raquel é de no máximo uns 3 pontos entre um município de repasse baixo e um de repasse alto, varia conforme o modelo e encolhe quando a aliança entra. Transferência e aliança andam juntas, mas os dados não dizem quem puxa quem.

### 6. A economia local não explica as diferenças de voto entre municípios
**Confiança alta para o que foi medido.**

Bolsa Família (nível e variação de 2022 para 2026), emprego formal no ano eleitoral (Novo CAGED) e renda per capita (Censo 2022) não mostram associação estável com o voto de Raquel por município.

O que isso não diz: a economia do estado melhorou entre 2022 e 2026 (PNAD: desemprego de 14,0% para 8,3%; renda domiciliar per capita +41% real de 2022 a 2025, contra +29% no Nordeste). Essa melhora é comum a todos os municípios, então não pode ser testada comparando um município com outro. A ausência de associação municipal não significa que a economia não pesou no resultado do estado.

## Síntese

O resultado de 2026 se organiza por território, município a município. Entre as variáveis medidas, a que mais acompanha essas diferenças é a aliança do prefeito, de forma robusta. Indicadores econômicos locais e repasses estaduais acompanham pouco ou nada. Os dados mostram associação; não provam que o prefeito causou o voto.

## Limites gerais

- Inferência ecológica em toda a análise de perfil e de movimento de eleitorados. No modelo hierárquico, as faixas medem a incerteza dentro do modelo, não o erro de usar dado agregado. Seis das 18 taxas não atingiram o critério formal de convergência (R-hat < 1,1), embora as cadeias difiram menos de 1 ponto; as taxas de Marília para Raquel, base da comparação por prefeito, passaram (R-hat ≤ 1,01). A linha de quem não votou em nenhum dos dois em 2022 fica de fora.
- Lista de alianças: só o Jamildo.com tem a lista por município; é a foto de 06/10/2026, sem categoria neutra, sem data de adesão; outras contagens divergem em até 5 municípios.
- Comparações entre eleições de natureza diferente (2º turno de 2022 x 1º turno de 2026).
- Transferências declaradas pelos próprios municípios ao Tesouro (SICONFI); qualidade da classificação varia.
- CAGED cobre só emprego com carteira; PNAD não desce a município.
- 184 municípios: pouco poder para desenhos quase-experimentais.

## O que fortaleceria as conclusões

- Pesquisa com eleitores (dado individual) que pergunte voto e avaliação do governo e do prefeito.
- A data em que cada prefeito declarou apoio, para ver se a adesão veio antes ou depois de repasses e de mudanças de popularidade.
- Repasses de 2023 e 2024 com os prefeitos daquele mandato (eleitos em 2020); a série atual usa a aliança dos prefeitos de 2025 em todos os anos.

## Referências de método usadas

- Rosen, O.; Jiang, W.; King, G.; Tanner, M. A. (2001). "Bayesian and Frequentist Inference for Ecological Inference: The R×C Case". *Statistica Neerlandica* 55(2): 134–156. doi 10.1111/1467-9574.00162.
- Novaes, L. M. (2018). "Disloyal Brokers and Weak Parties". *American Journal of Political Science* 62(1): 84–98. doi 10.1111/ajps.12331.
- Ventura, T. (2021). "Do mayors matter? Reverse coattails on congressional elections in Brazil". *Electoral Studies* 69: 102242. doi 10.1016/j.electstud.2020.102242.
- Feierherd, G. (2020). "How Mayors Hurt Their Presidential Ticket: Party Brands and Incumbency Spillovers in Brazil". *The Journal of Politics* 82(1): 195–210. doi 10.1086/705742.
- Cameron, A. C.; Gelbach, J. B.; Miller, D. L. (2008). "Bootstrap-Based Improvements for Inference with Clustered Errors". *Review of Economics and Statistics* 90(3): 414–427. doi 10.1162/rest.90.3.414.
- Gelman, A.; Rubin, D. B. (1992). "Inference from Iterative Simulation Using Multiple Sequences". *Statistical Science* 7(4). doi 10.1214/ss/1177011136.
- Lau, O.; Moore, R. T.; Kellermann, M. eiPack: Ecological Inference and Higher-Dimension Data Management. Pacote R, versão 0.2-2. doi 10.32614/CRAN.package.eiPack.
- Webb, M. D. (2023). "Reworking wild bootstrap-based inference for clustered errors". *Canadian Journal of Economics* 56(3): 839–858. doi 10.1111/caje.12661.
