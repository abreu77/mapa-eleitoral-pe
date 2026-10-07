# Resumo da inferência ecológica (src/inferencia_ecologica.R): convergência e tabelas.
#
# Lê resultados/inferencia_ecologica/cadeia_<grupo>_<semente>.rds (várias cadeias por grupo).
# Convergência: R-hat de Gelman-Rubin por célula (precisa ficar abaixo de 1,1) e tamanho efetivo.
# Tabelas: mediana e faixa p5–p95 juntando as cadeias; estado = os dois grupos ponderados pelos
# eleitores de cada origem; diferença = prefeito com Raquel menos prefeito com João.
#
# Rodar da raiz do projeto:  Rscript src/inferencia_ecologica_resumo.R

suppressMessages(library(coda))
DIR <- 'resultados/inferencia_ecologica'
arqs <- list.files(DIR, pattern = '^cadeia_[RJ]_\\d+\\.rds$', full.names = TRUE)
cad <- lapply(arqs, readRDS)
grupo <- sapply(cad, `[[`, 'grupo')
NOME <- c(R = 'Prefeito com Raquel', J = 'Prefeito com João')
LIN <- dimnames(cad[[1]]$taxa)[[1]]
COL <- dimnames(cad[[1]]$taxa)[[2]]

diag <- list()
for (g in c('R', 'J')) {
  cs <- cad[grupo == g]
  for (r in LIN) for (k in COL) {
    ml <- mcmc.list(lapply(cs, function(x) mcmc(x$taxa[r, k, ])))
    diag[[length(diag) + 1]] <- data.frame(grupo = NOME[[g]], origem = r, destino = k, cadeias = length(cs),
      rhat = gelman.diag(ml, autoburnin = FALSE)$psrf[1], n_efetivo = round(sum(effectiveSize(ml))),
      medianas_por_cadeia = paste(sprintf('%.1f', sapply(cs, function(x) median(x$taxa[r, k, ]))), collapse = ' / '))
  }
}
diag <- do.call(rbind, diag)

# amostras juntas por grupo (cadeias em sequência) e o estado: cadeia i de um grupo com cadeia i do outro
junta <- function(g) do.call(abind3, lapply(cad[grupo == g], `[[`, 'taxa'))
abind3 <- function(...) { l <- list(...); a <- array(unlist(l), c(dim(l[[1]])[1:2], sum(sapply(l, function(x) dim(x)[3]))))
  dimnames(a) <- dimnames(l[[1]])[1:2]; a }
tR <- junta('R'); tJ <- junta('J')
n <- min(dim(tR)[3], dim(tJ)[3]); tR <- tR[, , 1:n]; tJ <- tJ[, , 1:n]
pR <- cad[grupo == 'R'][[1]]$peso_origem; pJ <- cad[grupo == 'J'][[1]]$peso_origem
tE <- tR
for (r in seq_along(LIN)) tE[r, , ] <- (tR[r, , ] * pR[r] + tJ[r, , ] * pJ[r]) / (pR[r] + pJ[r])
tabs <- list('Estado' = tE, 'Prefeito com Raquel' = tR, 'Prefeito com João' = tJ, 'Diferença (Raquel − João)' = tR - tJ)
res <- do.call(rbind, lapply(names(tabs), function(g) do.call(rbind, lapply(LIN, function(r) do.call(rbind, lapply(COL, function(k) {
  x <- tabs[[g]][r, k, ]
  data.frame(grupo = g, origem = r, destino = k, mediana = median(x), p5 = quantile(x, .05), p95 = quantile(x, .95))
}))))))
res[, 4:6] <- round(res[, 4:6], 1)
write.csv(res, file.path(DIR, 'resumo.csv'), row.names = FALSE, fileEncoding = 'UTF-8')
write.csv(diag, file.path(DIR, 'convergencia.csv'), row.names = FALSE, fileEncoding = 'UTF-8')

cat('Cadeias por grupo:', paste(names(table(grupo)), table(grupo), collapse = ', '), '\n')
cat('R-hat máximo:', round(max(diag$rhat), 3), '| células com R-hat > 1,1:', sum(diag$rhat > 1.1),
    '| menor tamanho efetivo:', min(diag$n_efetivo), '\n\n')
print(diag, row.names = FALSE)
cat('\nDe cada 100 eleitores aptos de cada origem em 2022 T2, quantos foram para... em 2026 (mediana, p5–p95)\n')
res$txt <- sprintf('%.0f (%.0f–%.0f)', res$mediana, res$p5, res$p95)
print(reshape(res[, c('grupo', 'origem', 'destino', 'txt')], idvar = c('grupo', 'origem'), timevar = 'destino',
              direction = 'wide'), row.names = FALSE)
