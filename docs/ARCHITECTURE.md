# Arquitetura Tecnica

## Visao geral

O projeto implementa uma arquitetura analitica em 3 camadas sobre SQLite:

- `Bronze`: ingestao bruta e rastreavel dos arquivos de origem.
- `Silver`: padronizacao semantica, tipagem basica e limpeza.
- `Gold`: views analiticas para dashboards e notebooks.

## Fluxo de dados

```text
Data Sources (CSV/DBC/ZIP/ODS)
    -> data/bronze/*
    -> scripts/02_load_bronze_sqlite.py
         -> br_cadop
         -> br_benef_operadora_carteira
    -> scripts/03_transform_silver.py
         -> si_operadora
         -> si_beneficiarios_operadora
    -> scripts/04_build_gold.py
         -> go_benef_total_mes
         -> go_benef_por_operadora_mes
         -> go_market_share_mes
         -> go_top10_operadoras_ultimo_mes
         -> go_distribuicao_*_mes
    -> app.py / notebooks
```

## Componentes

### 1) Ingestao Bronze

Arquivo: `scripts/02_load_bronze_sqlite.py`

Responsabilidades:

- detectar encoding (`utf-8-sig`, `utf-8`, `latin-1`);
- detectar delimitador (`;`, `,`, `\t`, `|`);
- sanitizar nomes de coluna para padrao SQL-safe;
- recarregar tabelas Bronze de forma idempotente (`DROP + CREATE`);
- adicionar metadados de ingestao:
  - `_ingested_at`
  - `_source_file`
  - `_row_num`
- criar indices basicos para acelerar joins e filtros.

### 2) Transformacao Silver

Arquivo: `scripts/03_transform_silver.py`

Responsabilidades:

- construir `si_operadora` a partir de `br_cadop`;
- construir `si_beneficiarios_operadora` a partir de `br_benef_operadora_carteira`;
- padronizar `competencia` para data mensal (`YYYY-MM-DD`);
- remover registros invalidos (`competencia` ou `beneficiarios` nulos);
- criar indices de performance por `registro_ans` e `competencia`.

### 3) Modelagem Gold

Arquivo: `scripts/04_build_gold.py`

Responsabilidades:

- gerar views analiticas para consumo direto;
- encapsular metricas de market share e ranking;
- disponibilizar agregacoes do ultimo mes para distribuicoes por dimensao.

### 4) Consumo (Dashboard)

Arquivo: `app.py`

Responsabilidades:

- executar queries SQL diretamente no SQLite;
- oferecer filtros de competencia e Top N;
- exibir KPIs, graficos e tabelas de dinamica competitiva;
- calcular HHI e classificar concentracao de mercado.

## Decisoes de arquitetura

- Banco local SQLite para simplicidade e portabilidade.
- Views Gold para reduzir duplicacao de SQL entre app e notebooks.
- Scripts versionados por etapa (`02`, `03`, `04`) para facilitar execucao sequencial.
- Camada Bronze reprocessavel para garantir reproducibilidade.

## Limites conhecidos

- Dependencia de arquivo local `database/ans.db`.
- Parte dos dados de `data/bronze/` nao esta integrada ao pipeline atual (foco principal em CADOP + beneficiarios por operadora).
- Sem orquestracao automatica nativa (execucao manual por scripts).

## Evolucao sugerida

- adicionar testes de qualidade de dados (ex.: Great Expectations, checks SQL);
- mover SQL do app para arquivos em `queries/`;
- empacotar dependencias em `requirements.txt`;
- criar rotina de atualizacao automatica de dados.
