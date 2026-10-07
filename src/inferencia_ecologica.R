# Para onde foram os eleitores de 2022 T2 em 2026: inferência ecológica hierárquica, por grupo de municípios.
#
# Modelo Multinomial-Dirichlet de Rosen, Jiang, King e Tanner (2001), pacote eiPack (ei.MD.bayes),
# sem covariável: cada seção tem as suas taxas de transição, tiradas de uma distribuição comum ao grupo.
# Roda à parte para municípios de prefeito com Raquel e de prefeito com João (aliança de 2026).
#
# Primeira versão (06/10/2026): tabela 4x4 com a aliança como covariável, em todas as seções juntas.
# Não convergiu (duas cadeias, R-hat de 2,8 a 90); o manual do eiPack avisa que a covariável deixa a
# cadeia muito lenta. Esta versão simplifica: 3x3 e sem covariável, um modelo por grupo.
#
# Base: eleitorado apto da seção.
# Linhas (2022 T2): Raquel, Marília, nenhum (outros + branco + nulo + abstenção), em fração dos aptos de 2022.
# Colunas (2026): Raquel, João, nenhum, em eleitores (somam os aptos de 2026).
# Seções: existem nas duas eleições, não são de trânsito, não mudaram de local.
# Não modela entrada e saída do eleitorado (novos eleitores, óbitos, transferências).
#
# Rodar da raiz do projeto (uma cadeia por chamada; várias em paralelo):
#   Rscript src/inferencia_ecologica.R <grupo R|J> <semente> [burnin] [thin] [amostras] [ajustes]
# Depois: Rscript src/inferencia_ecologica_resumo.R (convergência e tabelas).

suppressMessages(library(eiPack))

arg <- commandArgs(trailingOnly = TRUE)
grupo <- arg[1]
par <- c(semente = 1, burnin = 3000, thin = 5, amostras = 400, ajustes = 3)
if (length(arg) > 1) par[seq_along(arg[-1])] <- as.numeric(arg[-1])
set.seed(par[['semente']])
ALIANCA <- c(R = 'Raquel Lyra', J = 'João Campos')[[grupo]]

L <- 'dados_limpos'
SAIDA <- 'resultados/inferencia_ecologica'
dir.create(SAIDA, showWarnings = FALSE, recursive = TRUE)
LINHAS <- c('Raquel', 'Marília', 'Nenhum')
COLUNAS <- c('Raquel', 'João', 'Nenhum')   # a última é a referência do modelo

sec <- read.csv(file.path(L, 'secoes.csv'), colClasses = c(cd_municipio = 'character'))
votos <- read.csv(file.path(L, 'votos_secao_longo.csv'), colClasses = c(nr_votavel = 'character'))
mun <- read.csv(file.path(L, 'municipios.csv'), colClasses = c(cd_tse = 'character'))
chave <- function(d) paste(d$nr_zona, d$nr_secao)

# eleitores de cada opção por seção; "Nenhum" = aptos menos os votos nos dois candidatos
fatias <- function(el, nr_a, nr_b, nomes) {
  v <- votos[votos$eleicao == el, ]
  s <- sec[sec$eleicao == el, ]
  rownames(s) <- chave(s)
  a <- tapply(v$qt_votos[v$nr_votavel == nr_a], chave(v)[v$nr_votavel == nr_a], sum)
  b <- tapply(v$qt_votos[v$nr_votavel == nr_b], chave(v)[v$nr_votavel == nr_b], sum)
  t <- data.frame(a = a[rownames(s)], b = b[rownames(s)], row.names = rownames(s))
  t[is.na(t)] <- 0
  t$nenhum <- s$aptos - t$a - t$b
  names(t) <- nomes
  list(contagem = as.matrix(t), aptos = s$aptos)
}

base <- sec[sec$eleicao == '2026T1' & sec$situacao == 'nas_duas' & !as.logical(sec$transito) &
              !as.logical(sec$mudou_local), c('nr_zona', 'nr_secao', 'cd_municipio')]
base <- merge(base, mun[, c('cd_tse', 'alianca_prefeito')], by.x = 'cd_municipio', by.y = 'cd_tse')
base <- base[base$alianca_prefeito == ALIANCA, ]
rownames(base) <- chave(base)

o <- fatias('2022T2', '45', '77', LINHAS)
d <- fatias('2026T1', '55', '40', COLUNAS)
ids <- Reduce(intersect, list(rownames(base), rownames(o$contagem), rownames(d$contagem)))
X <- o$contagem[ids, ] / rowSums(o$contagem[ids, ])
Y <- d$contagem[ids, ]
stopifnot(all(Y >= 0), all(X >= 0))
dados <- data.frame(r_raquel = X[, 1], r_marilia = X[, 2], r_nenhum = X[, 3],
                    c_raquel = Y[, 1], c_joao = Y[, 2], c_nenhum = Y[, 3], total = rowSums(Y))
cat(sprintf('Prefeito com %s: %d seções, %d municípios; semente %d\n', ALIANCA, nrow(dados),
            length(unique(base[ids, 'cd_municipio'])), par[['semente']]))

formula <- cbind(c_raquel, c_joao, c_nenhum) ~ cbind(r_raquel, r_marilia, r_nenhum)
t0 <- Sys.time()
ajuste <- tuneMD(formula, data = dados, total = 'total', ntunes = par[['ajustes']], totaldraws = 500)
fit <- ei.MD.bayes(formula, total = 'total', data = dados, tune.list = ajuste, sample = par[['amostras']],
                   thin = par[['thin']], burnin = par[['burnin']], ret.beta = 'r', ret.mcmc = FALSE)
cat('tempo:', format(round(Sys.time() - t0, 1)), '\n')

# taxas do grupo por amostra: média das seções, ponderada pelos eleitores de cada origem
B <- fit$draws$Beta                                     # linhas x colunas x seções x amostras
peso <- X * dados$total
taxa <- array(NA, c(3, 3, dim(B)[4]), list(LINHAS, COLUNAS, NULL))
for (r in 1:3) {
  w <- peso[, r] / sum(peso[, r])
  for (k in 1:3) taxa[r, k, ] <- colSums(B[r, k, , ] * w) * 100
}
saveRDS(list(grupo = grupo, par = par, taxa = taxa, peso_origem = colSums(peso),
             secoes = nrow(dados), alpha = fit$draws$Alpha, acc = fit$acc.ratios),
        file.path(SAIDA, sprintf('cadeia_%s_%d.rds', grupo, par[['semente']])))
cat('mediana das taxas (linha = 2022 T2, coluna = 2026):\n')
print(round(apply(taxa, 1:2, median), 1))
