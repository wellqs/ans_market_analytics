# Modelo de Dados

## Convencoes

- Prefixo `br_`: camada Bronze (raw/staging).
- Prefixo `si_`: camada Silver (dados tratados).
- Prefixo `go_`: camada Gold (views analiticas).
- Chave operacional principal entre tabelas: `registro_ans`.

## Camada Bronze

### br_cadop

Origem: `data/bronze/operadoras/Relatorio_cadop.csv`

Descricao: cadastro bruto das operadoras.

Colunas relevantes usadas na Silver:

- `registro_operadora`
- `cnpj`
- `razao_social`
- `nome_fantasia`
- `modalidade`
- `cidade`
- `uf`
- `regiao_de_comercializacao`
- `data_registro_ans`
- `_ingested_at`, `_source_file`, `_row_num`

### br_benef_operadora_carteira

Origem: `data/bronze/beneficiarios_operadora/Beneficiarios_operadora_e_carteira.csv`

Descricao: historico bruto de beneficiarios por operadora e dimensoes de carteira.

Colunas relevantes usadas na Silver:

- `cd_operadora`
- `id_cmpt`
- `nr_benef`
- `gr_modalidade`
- `gr_contratacao`
- `cobertura`
- `tipo_financiamento`
- `vigencia_plano`
- `_ingested_at`, `_source_file`, `_row_num`

## Camada Silver

### si_operadora

Descricao: dimensao tratada de operadoras.

Campos principais:

- `registro_ans` (texto, chave de negocio)
- `cnpj`
- `razao_social`
- `nome_fantasia`
- `modalidade`
- `cidade`
- `uf`
- `regiao_de_comercializacao`
- `data_registro_ans`
- `ingested_at`
- `source_file`

Indice:

- `idx_si_operadora_registro_ans` em `registro_ans`

### si_beneficiarios_operadora

Descricao: fato mensal de beneficiarios por operadora.

Campos principais:

- `registro_ans`
- `competencia` (normalizada para `YYYY-MM-DD`)
- `beneficiarios` (inteiro)
- `modalidade_grupo`
- `contratacao_grupo`
- `cobertura`
- `financiamento`
- `vigencia_plano`
- `ingested_at`
- `source_file`

Regras de padronizacao de `competencia`:

- `YYYYMM` -> `YYYY-MM-01`
- `YYYY-MM` -> `YYYY-MM-01`
- `YYYY-MM-DD` -> mantem
- fora desse padrao -> `NULL` (registro removido)

Indices:

- `idx_si_benef_registro_ans`
- `idx_si_benef_competencia`
- `idx_si_benef_comp_reg`

## Camada Gold (views)

### go_benef_total_mes

Total de beneficiarios do setor por competencia.

- granularidade: 1 linha por mes

### go_benef_por_operadora_mes

Total de beneficiarios por operadora e competencia.

- granularidade: 1 linha por `competencia + registro_ans`

### go_market_share_mes

Market share e ranking por operadora em cada mes.

- metrica principal: `market_share_pct`
- ranking: `rank_mes` (DENSE_RANK decrescente por beneficiarios)

### go_top10_operadoras_ultimo_mes

Recorte do top 10 por market share no ultimo mes disponivel.

### go_distribuicao_modalidade_grupo_mes
### go_distribuicao_contratacao_grupo_mes
### go_distribuicao_cobertura_mes
### go_distribuicao_financiamento_mes

Distribuicoes de beneficiarios por dimensao no ultimo mes disponivel.

## Relacao entre entidades

```text
si_operadora (1) ---- (N) si_beneficiarios_operadora
        |                          |
        +------ usado em ----------+
                 go_market_share_mes
```

## Qualidade e consistencia

Validacoes atuais no projeto:

- exclusao de linhas sem chave de operadora na Silver;
- exclusao de linhas com `competencia` invalida;
- exclusao de linhas com `beneficiarios` nulo;
- scripts auxiliares de inspecao:
  - `scripts/inspect_tables.py`
  - `scripts/check_silver.py`
