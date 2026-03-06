# Runbook Operacional

## Finalidade

Guia de operacao do pipeline e dashboard para ambiente local.

## Pre-requisitos

- Python 3.10+
- SQLite (ja embutido no Python)
- Dependencias Python:
  - `streamlit`
  - `plotly`

## Setup inicial

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install streamlit plotly
```

## Execucao do pipeline

Ordem recomendada:

1. Bronze

```powershell
python scripts/02_load_bronze_sqlite.py
```

2. Silver

```powershell
python scripts/03_transform_silver.py
```

3. Gold

```powershell
python scripts/04_build_gold.py
```

Resultado esperado:

- banco atualizado em `database/ans.db`;
- tabelas `si_*` recriadas;
- views `go_*` recriadas.

## Subir o dashboard

```powershell
streamlit run app.py
```

A aplicacao abre no navegador local com:

- filtro de `competencia`;
- controle de `Top N operadoras`;
- KPIs de total, variacao e HHI;
- tabelas e graficos de ranking e dinamica competitiva.

## Verificacoes rapidas

### Conferir esquema Bronze

```powershell
python scripts/inspect_tables.py
```

### Conferir volumes Silver

```powershell
python scripts/check_silver.py
```

### Conferir status Git

```powershell
git status --short --branch
```

## Troubleshooting

### 1) Erro de arquivo ausente no Bronze

Sintoma: `FileNotFoundError` no script `02_load_bronze_sqlite.py`.

Acao:

- confirmar existencia dos arquivos:
  - `data/bronze/operadoras/Relatorio_cadop.csv`
  - `data/bronze/beneficiarios_operadora/Beneficiarios_operadora_e_carteira.csv`

### 2) Dashboard sem dados

Sintoma: mensagem de nenhuma competencia encontrada.

Acao:

- executar pipeline completo (`02`, `03`, `04`);
- validar se `si_beneficiarios_operadora` foi populada.

### 3) Performance lenta

Acao:

- garantir que scripts de transformacao criaram indices;
- evitar abrir banco em rede lenta;
- considerar migracao para motor cliente-servidor em datasets maiores.

## Boas praticas de operacao

- rodar pipeline sempre na ordem `02 -> 03 -> 04`;
- versionar somente codigo/documentacao (nao versionar `database/*.db`);
- registrar data de atualizacao dos dados em release notes.

## Rotina sugerida (semanal/mensal)

1. Atualizar arquivos de origem em `data/bronze`.
2. Executar pipeline completo.
3. Validar metricas no dashboard.
4. Commitar scripts/notebooks/docs alterados.
5. Publicar no repositorio remoto.
