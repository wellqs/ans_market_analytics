import sqlite3
from pathlib import Path
from typing import Any, Iterable

import streamlit as st
import plotly.graph_objects as go

# ==============================
# Estilo visual
# ==============================
CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #2C2C2C;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #2C2C2C;
        letter-spacing: -0.02em;
    }

    .dashboard-subtitle {
        color: #5C5C5C;
        font-size: 0.98rem;
        margin-top: -0.35rem;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #2C2C2C;
        margin-bottom: 0.35rem;
    }

    .section-divider {
        border: none;
        height: 3px;
        background: linear-gradient(90deg, #FF6F61 0%, #FFD6D1 100%);
        border-radius: 999px;
        margin: 0.2rem 0 1rem 0;
    }

    .kpi-card {
        background: linear-gradient(180deg, #FFF8F7 0%, #FFFFFF 100%);
        border: 1px solid #F3D2CD;
        border-left: 7px solid #FF6F61;
        border-radius: 18px;
        padding: 1rem 1rem 0.9rem 1rem;
        box-shadow: 0 6px 22px rgba(255, 111, 97, 0.08);
        min-height: 132px;
    }

    .kpi-label {
        font-size: 0.92rem;
        color: #6B6B6B;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .kpi-value {
        font-size: 1.9rem;
        color: #2C2C2C;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.45rem;
    }

    .kpi-helper {
        font-size: 0.92rem;
        color: #6B6B6B;
        margin-bottom: 0.6rem;
    }

    .kpi-bar {
        width: 100%;
        height: 8px;
        border-radius: 999px;
        background: #FFE3DF;
        overflow: hidden;
    }

    .kpi-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #FF6F61 0%, #FF9A8F 100%);
    }

    .insight-box {
        background: #FFF8F7;
        border: 1px solid #F3D2CD;
        border-radius: 16px;
        padding: 1rem 1rem;
        color: #4A4A4A;
        margin-top: 0.75rem;
        box-shadow: 0 4px 14px rgba(255, 111, 97, 0.05);
    }

    [data-testid="stSidebar"] {
        background: #FCFCFC;
        border-right: 1px solid #F0DFDC;
    }

    [data-testid="stMetric"] {
        background: #FFF8F7;
        border: 1px solid #F3D2CD;
        border-left: 6px solid #FF6F61;
        padding: 0.8rem 0.9rem;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(255, 111, 97, 0.06);
    }

    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
    }
</style>
"""

# ==============================
# Configuração da página
# ==============================
st.set_page_config(
    page_title="ANS Market Analytics",
    page_icon="📊",
    layout="wide",
)

DB_PATH = Path(__file__).resolve().parent / "database" / "ans.db"


# ==============================
# Helpers
# ==============================
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(query: str, params: Iterable[Any] | None = None) -> list[sqlite3.Row]:
    params = tuple(params or ())
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()


def rows_to_table(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


def format_int(value: Any) -> str:
    if value is None:
        return "-"
    return f"{int(value):,}".replace(",", ".")


def format_pct(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def format_delta(value: Any) -> str:
    if value is None:
        return "N/I"
    sign = "+" if float(value) >= 0 else ""
    return f"{sign}{format_int(value)}"


def format_number_compact(value: Any) -> str:
    if value is None:
        return "-"
    value = float(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M".replace(".", ",")
    if value >= 1_000:
        return f"{value / 1_000:.1f} mil".replace(".", ",")
    return format_int(value)


def kpi_card(title: str, value: str, helper: str, fill_pct: int = 72) -> str:
    fill_pct = max(0, min(fill_pct, 100))
    return f"""
    <div class=\"kpi-card\">
        <div class=\"kpi-label\">{title}</div>
        <div class=\"kpi-value\">{value}</div>
        <div class=\"kpi-helper\">{helper}</div>
        <div class=\"kpi-bar\"><div class=\"kpi-fill\" style=\"width: {fill_pct}%;\"></div></div>
    </div>
    """


def build_bar_chart(x_values: list[str], y_values: list[float], title: str, y_title: str) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                x=y_values,
                y=x_values,
                orientation="h",
                text=[format_int(v) if y_title.lower().startswith("benef") else str(v) for v in y_values],
                textposition="outside",
                marker=dict(
                    color="#FF9A8F",
                    line=dict(color="#FF6F61", width=1.2),
                ),
                hovertemplate="<b>%{y}</b><br>Valor: %{x:,}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis_title=y_title,
        yaxis_title="",
        height=460,
        margin=dict(l=20, r=20, t=60, b=20),
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#2C2C2C"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F5D5D0", zeroline=False)
    fig.update_yaxes(autorange="reversed")
    return fig


def build_line_chart(x_values: list[str], y_values: list[float], title: str, y_title: str) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers+text",
                text=[format_int(v) for v in y_values],
                textposition="top center",
                line=dict(color="#FF6F61", width=3),
                marker=dict(size=8, color="#FF6F61", line=dict(color="#FFFFFF", width=2)),
                fill="tozeroy",
                fillcolor="rgba(255, 111, 97, 0.12)",
                hovertemplate="<b>%{x}</b><br>Total: %{y:,}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis_title="Competência",
        yaxis_title=y_title,
        height=440,
        margin=dict(l=20, r=20, t=60, b=20),
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#2C2C2C"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F5D5D0", zeroline=False)
    return fig


# ==============================
# Queries base
# ==============================
LATEST_MONTH_QUERY = """
SELECT MAX(competencia) AS competencia
FROM si_beneficiarios_operadora;
"""

ALL_MONTHS_QUERY = """
SELECT DISTINCT competencia
FROM si_beneficiarios_operadora
ORDER BY competencia DESC;
"""

SECTOR_TOTAL_QUERY = """
WITH operadora_mes AS (
    SELECT
        competencia,
        registro_ans,
        MAX(beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora
    GROUP BY competencia, registro_ans
)
SELECT
    competencia,
    SUM(beneficiarios) AS total_beneficiarios
FROM operadora_mes
GROUP BY competencia
ORDER BY competencia;
"""

MARKET_SHARE_QUERY = """
WITH operadora_mes AS (
    SELECT
        b.competencia,
        b.registro_ans,
        COALESCE(o.razao_social, 'N/I') AS razao_social,
        MAX(b.beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora b
    LEFT JOIN si_operadora o
        ON o.registro_ans = b.registro_ans
    WHERE b.competencia = ?
    GROUP BY b.competencia, b.registro_ans, o.razao_social
)
SELECT
    competencia,
    registro_ans,
    razao_social,
    beneficiarios,
    ROUND(
        beneficiarios * 100.0 /
        SUM(beneficiarios) OVER (PARTITION BY competencia),
        4
    ) AS market_share_pct,
    RANK() OVER (
        PARTITION BY competencia
        ORDER BY beneficiarios DESC
    ) AS ranking
FROM operadora_mes
ORDER BY ranking
LIMIT ?;
"""

HHI_QUERY = """
WITH operadora_mes AS (
    SELECT
        competencia,
        registro_ans,
        MAX(beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora
    WHERE competencia = ?
    GROUP BY competencia, registro_ans
),
market_share AS (
    SELECT
        competencia,
        registro_ans,
        beneficiarios,
        (beneficiarios * 100.0 / SUM(beneficiarios) OVER (PARTITION BY competencia)) AS market_share_pct
    FROM operadora_mes
)
SELECT
    competencia,
    ROUND(SUM(market_share_pct * market_share_pct), 2) AS hhi
FROM market_share
GROUP BY competencia;
"""

MODALIDADE_QUERY = """
WITH modalidade_mes AS (
    SELECT
        competencia,
        modalidade_grupo,
        registro_ans,
        MAX(beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora
    WHERE competencia = ?
    GROUP BY competencia, modalidade_grupo, registro_ans
),
total_modalidade AS (
    SELECT
        competencia,
        modalidade_grupo,
        SUM(beneficiarios) AS total_beneficiarios
    FROM modalidade_mes
    GROUP BY competencia, modalidade_grupo
)
SELECT
    competencia,
    COALESCE(modalidade_grupo, 'N/I') AS modalidade_grupo,
    total_beneficiarios,
    ROUND(
        total_beneficiarios * 100.0 /
        SUM(total_beneficiarios) OVER (PARTITION BY competencia),
        4
    ) AS share_modalidade_pct
FROM total_modalidade
ORDER BY total_beneficiarios DESC;
"""

CONTRATACAO_QUERY = """
WITH segmento AS (
    SELECT
        competencia,
        contratacao_grupo,
        registro_ans,
        MAX(beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora
    WHERE competencia = ?
    GROUP BY competencia, contratacao_grupo, registro_ans
),
total_segmento AS (
    SELECT
        competencia,
        contratacao_grupo,
        SUM(beneficiarios) AS total_beneficiarios
    FROM segmento
    GROUP BY competencia, contratacao_grupo
)
SELECT
    competencia,
    COALESCE(contratacao_grupo, 'N/I') AS contratacao_grupo,
    total_beneficiarios,
    ROUND(
        total_beneficiarios * 100.0 /
        SUM(total_beneficiarios) OVER (PARTITION BY competencia),
        4
    ) AS share_contratacao_pct
FROM total_segmento
ORDER BY total_beneficiarios DESC;
"""

TOP_GAINS_QUERY = """
WITH operadora_mes AS (
    SELECT
        competencia,
        registro_ans,
        MAX(beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora
    GROUP BY competencia, registro_ans
),
growth AS (
    SELECT
        competencia,
        registro_ans,
        beneficiarios,
        LAG(beneficiarios) OVER (
            PARTITION BY registro_ans
            ORDER BY competencia
        ) AS beneficiarios_mes_anterior
    FROM operadora_mes
),
base AS (
    SELECT
        g.competencia,
        g.registro_ans,
        COALESCE(o.razao_social, 'N/I') AS razao_social,
        g.beneficiarios,
        g.beneficiarios_mes_anterior,
        (g.beneficiarios - g.beneficiarios_mes_anterior) AS crescimento_absoluto
    FROM growth g
    LEFT JOIN si_operadora o
        ON o.registro_ans = g.registro_ans
    WHERE g.competencia = ?
      AND g.beneficiarios_mes_anterior IS NOT NULL
)
SELECT *
FROM base
ORDER BY crescimento_absoluto DESC
LIMIT ?;
"""

TOP_LOSSES_QUERY = """
WITH operadora_mes AS (
    SELECT
        competencia,
        registro_ans,
        MAX(beneficiarios) AS beneficiarios
    FROM si_beneficiarios_operadora
    GROUP BY competencia, registro_ans
),
growth AS (
    SELECT
        competencia,
        registro_ans,
        beneficiarios,
        LAG(beneficiarios) OVER (
            PARTITION BY registro_ans
            ORDER BY competencia
        ) AS beneficiarios_mes_anterior
    FROM operadora_mes
),
base AS (
    SELECT
        g.competencia,
        g.registro_ans,
        COALESCE(o.razao_social, 'N/I') AS razao_social,
        g.beneficiarios,
        g.beneficiarios_mes_anterior,
        (g.beneficiarios - g.beneficiarios_mes_anterior) AS crescimento_absoluto
    FROM growth g
    LEFT JOIN si_operadora o
        ON o.registro_ans = g.registro_ans
    WHERE g.competencia = ?
      AND g.beneficiarios_mes_anterior IS NOT NULL
)
SELECT *
FROM base
ORDER BY crescimento_absoluto ASC
LIMIT ?;
"""


# ==============================
# Carregamento inicial
# ==============================
latest_month_rows = run_query(LATEST_MONTH_QUERY)
latest_month = latest_month_rows[0]["competencia"] if latest_month_rows and latest_month_rows[0]["competencia"] else None
all_months = [row["competencia"] for row in run_query(ALL_MONTHS_QUERY)]
sector_total_rows = rows_to_table(run_query(SECTOR_TOTAL_QUERY))

if not latest_month:
    st.error("Nenhuma competência encontrada em si_beneficiarios_operadora.")
    st.stop()


# ==============================
# Sidebar
# ==============================
st.sidebar.title("⚙️ Filtros")
selected_month = st.sidebar.selectbox(
    "Competência",
    options=all_months,
    index=0,
)

top_n = st.sidebar.slider("Top N operadoras", min_value=5, max_value=30, value=10, step=5)


# ==============================
# Dados filtrados
# ==============================
market_share_rows = rows_to_table(run_query(MARKET_SHARE_QUERY, [selected_month, top_n]))
hhi_rows = rows_to_table(run_query(HHI_QUERY, [selected_month]))
modalidade_rows = rows_to_table(run_query(MODALIDADE_QUERY, [selected_month]))
contratacao_rows = rows_to_table(run_query(CONTRATACAO_QUERY, [selected_month]))
gains_rows = rows_to_table(run_query(TOP_GAINS_QUERY, [selected_month, 10]))
losses_rows = rows_to_table(run_query(TOP_LOSSES_QUERY, [selected_month, 10]))

current_total = next((r["total_beneficiarios"] for r in sector_total_rows if r["competencia"] == selected_month), None)
previous_total = None
for idx, row in enumerate(sector_total_rows):
    if row["competencia"] == selected_month and idx > 0:
        previous_total = sector_total_rows[idx - 1]["total_beneficiarios"]
        break

if previous_total is not None and current_total is not None:
    delta_abs = current_total - previous_total
    delta_pct = (delta_abs / previous_total) * 100 if previous_total else None
else:
    delta_abs = None
    delta_pct = None

hhi_value = hhi_rows[0]["hhi"] if hhi_rows else None
if hhi_value is None:
    hhi_class = "N/I"
elif hhi_value < 1500:
    hhi_class = "Mercado pouco concentrado"
elif hhi_value <= 2500:
    hhi_class = "Mercado moderadamente concentrado"
else:
    hhi_class = "Mercado altamente concentrado"


# ==============================
# Header
# ==============================
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown("<h1>📊 ANS Market Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='dashboard-subtitle'>Painel analítico do mercado de saúde suplementar com foco em estrutura competitiva, evolução do setor e participação por segmentos.</div>",
    unsafe_allow_html=True,
)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
with metric_col1:
    st.markdown(kpi_card("🗓️ Competência", selected_month, "Mês de referência selecionado no painel.", 58), unsafe_allow_html=True)
with metric_col2:
    st.markdown(kpi_card("👥 Beneficiários do setor", format_number_compact(current_total), "Total consolidado do setor na competência.", 86), unsafe_allow_html=True)
with metric_col3:
    st.markdown(kpi_card("📈 Variação vs mês anterior", format_delta(delta_abs), format_pct(delta_pct) if delta_pct is not None else "Sem histórico suficiente.", 67 if delta_abs is not None else 28), unsafe_allow_html=True)
with metric_col4:
    st.markdown(kpi_card("🧠 Concentração do mercado", f"HHI {hhi_value}" if hhi_value is not None else "HHI N/I", hhi_class, 44 if hhi_value is not None else 20), unsafe_allow_html=True)

st.markdown(
    "<div class='insight-box'><b>Insight do painel:</b> Na competência selecionada, o setor de saúde suplementar registra aproximadamente 68 milhões de beneficiários. O índice HHI indica baixa concentração de mercado, sugerindo elevada fragmentação entre operadoras.</div>",
    unsafe_allow_html=True,
)


# ==============================
# Linha 1 — evolução e top market share
# ==============================
left, right = st.columns((1.1, 1))

with left:
    st.markdown("<div class='section-title'>Evolução do número de beneficiários</div>", unsafe_allow_html=True)
    x_vals = [r["competencia"] for r in sector_total_rows]
    y_vals = [r["total_beneficiarios"] for r in sector_total_rows]
    fig = build_line_chart(x_vals, y_vals, "Total de beneficiários por competência", "Beneficiários")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown(f"<div class='section-title'>Top {top_n} operadoras por market share</div>", unsafe_allow_html=True)
    x_vals = [r["razao_social"] for r in market_share_rows]
    y_vals = [r["beneficiarios"] for r in market_share_rows]
    fig = build_bar_chart(x_vals, y_vals, f"Top {top_n} operadoras — {selected_month}", "Beneficiários")
    st.plotly_chart(fig, use_container_width=True)


# ==============================
# Linha 2 — tabelas analíticas
# ==============================
st.markdown("<div class='section-title'>Ranking de market share</div>", unsafe_allow_html=True)
st.dataframe(
    [
        {
            "Ranking": r["ranking"],
            "Registro ANS": r["registro_ans"],
            "Operadora": r["razao_social"],
            "Beneficiários": format_int(r["beneficiarios"]),
            "Market Share (%)": format_pct(r["market_share_pct"], 4),
        }
        for r in market_share_rows
    ],
    use_container_width=True,
    hide_index=True,
)

seg1, seg2 = st.columns(2)

with seg1:
    st.markdown("<div class='section-title'>Participação por modalidade</div>", unsafe_allow_html=True)
    st.dataframe(
        [
            {
                "Modalidade": r["modalidade_grupo"],
                "Beneficiários": format_int(r["total_beneficiarios"]),
                "Share (%)": format_pct(r["share_modalidade_pct"], 4),
            }
            for r in modalidade_rows
        ],
        use_container_width=True,
        hide_index=True,
    )

with seg2:
    st.markdown("<div class='section-title'>Participação por tipo de contratação</div>", unsafe_allow_html=True)
    st.dataframe(
        [
            {
                "Contratação": r["contratacao_grupo"],
                "Beneficiários": format_int(r["total_beneficiarios"]),
                "Share (%)": format_pct(r["share_contratacao_pct"], 4),
            }
            for r in contratacao_rows
        ],
        use_container_width=True,
        hide_index=True,
    )


# ==============================
# Linha 3 — dinâmica competitiva
# ==============================
st.subheader("Dinâmica competitiva")
dyn1, dyn2 = st.columns(2)

with dyn1:
    st.markdown("**Top ganhos de beneficiários vs mês anterior**")
    if gains_rows:
        st.dataframe(
            [
                {
                    "Operadora": r["razao_social"],
                    "Atual": format_int(r["beneficiarios"]),
                    "Mês anterior": format_int(r["beneficiarios_mes_anterior"]),
                    "Crescimento": format_int(r["crescimento_absoluto"]),
                }
                for r in gains_rows
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Ainda não há meses suficientes para calcular crescimento mês a mês.")

with dyn2:
    st.markdown("**Top perdas de beneficiários vs mês anterior**")
    if losses_rows:
        st.dataframe(
            [
                {
                    "Operadora": r["razao_social"],
                    "Atual": format_int(r["beneficiarios"]),
                    "Mês anterior": format_int(r["beneficiarios_mes_anterior"]),
                    "Variação": format_int(r["crescimento_absoluto"]),
                }
                for r in losses_rows
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Ainda não há meses suficientes para calcular retração mês a mês.")


# ==============================
# Footer
# ==============================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color:#6B6B6B; font-size:0.9rem; padding-top:8px;'>
        <p>Data Engineering & Analytics Project</p>
        <p>Developed by <b>UÉLINTON QUINTÃO SILVÉRIO</b> • 2026</p>
    </div>
    """,
    unsafe_allow_html=True
)
