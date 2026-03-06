# ANS Market Analytics

Projeto de analytics para o mercado de saude suplementar brasileiro com dados da ANS, estruturado em pipeline `Bronze -> Silver -> Gold`, persistido em SQLite e exposto em dashboard Streamlit.

## Objetivo

Entregar uma base analitica reproduzivel para:

- acompanhar evolucao de beneficiarios por competencia;
- medir market share por operadora;
- avaliar concentracao de mercado via HHI;
- analisar distribuicao por modalidade e tipo de contratacao;
- observar ganhos e perdas mensais de beneficiarios.

## Escopo atual

- Ingestao de duas fontes principais para camada Bronze:
  - `Relatorio_cadop.csv` (cadastro de operadoras);
  - `Beneficiarios_operadora_e_carteira.csv` (beneficiarios por operadora/carteira).
- Transformacao para camadas Silver (`si_*`) com padronizacao de chaves e datas.
- Materializacao de views Gold (`go_*`) para consumo analitico.
- Dashboard Streamlit em `app.py` com filtros, KPIs, tabelas e graficos.
- Caderno de analise em `notebooks/` para validacao e exploracao.

## Arquitetura (resumo)

```text
Arquivos brutos (CSV/DBC/ZIP/ODS) em data/bronze
        |
        v
scripts/02_load_bronze_sqlite.py
  -> tabelas br_* no SQLite
        |
        v
scripts/03_transform_silver.py
  -> tabelas si_operadora e si_beneficiarios_operadora
        |
        v
scripts/04_build_gold.py
  -> views go_* para analise
        |
        v
app.py (Streamlit + Plotly)
```

Documentacao detalhada:

- [Arquitetura](docs/ARCHITECTURE.md)
- [Modelo de dados](docs/DATA_MODEL.md)
- [Runbook operacional](docs/RUNBOOK.md)

## Estrutura do repositorio

```text
ans_market_analytics/
├─ app.py
├─ database/
│  └─ ans.db
├─ data/
│  ├─ bronze/
│  ├─ silver/
│  └─ gold/
├─ scripts/
│  ├─ 02_load_bronze_sqlite.py
│  ├─ 03_transform_silver.py
│  ├─ 04_build_gold.py
│  ├─ check_silver.py
│  └─ inspect_tables.py
├─ notebooks/
└─ docs/
```

## Requisitos

- Python 3.10+ (recomendado 3.11)
- Pacotes:
  - `streamlit`
  - `plotly`

Instalacao sugerida:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install streamlit plotly
```

## Como executar

1. Carregar Bronze no SQLite:

```powershell
python scripts/02_load_bronze_sqlite.py
```

2. Gerar Silver:

```powershell
python scripts/03_transform_silver.py
```

3. Gerar Gold:

```powershell
python scripts/04_build_gold.py
```

4. Subir dashboard:

```powershell
streamlit run app.py
```

## Entidades principais

- `br_cadop`: staging bruto do cadastro de operadoras.
- `br_benef_operadora_carteira`: staging bruto de beneficiarios.
- `si_operadora`: dimensao de operadoras tratada.
- `si_beneficiarios_operadora`: fato mensal por operadora com `competencia` padronizada.
- `go_market_share_mes`: market share mensal com ranking.
- `go_top10_operadoras_ultimo_mes`: top 10 no ultimo mes.

## Observacoes importantes

- O app depende do banco em `database/ans.db`.
- `competencia` e padronizada para formato `YYYY-MM-DD`.
- O projeto possui dados grandes; para evolucao futura, considerar particionamento e/ou Git LFS para artefatos pesados.

## Proximos incrementos recomendados

- Adicionar `requirements.txt` ou `pyproject.toml`.
- Criar testes automatizados para qualidade das transformacoes.
- Externalizar queries SQL para arquivos em `queries/`.
- Automatizar pipeline via tarefa agendada (ex.: GitHub Actions, cron ou Airflow).
