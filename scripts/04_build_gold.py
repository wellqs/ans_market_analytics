import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ans.db")

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # Limpa views antigas (idempotente)
    for v in [
        "go_benef_total_mes",
        "go_benef_por_operadora_mes",
        "go_market_share_mes",
        "go_top10_operadoras_ultimo_mes",
        "go_distribuicao_modalidade_grupo_mes",
        "go_distribuicao_contratacao_grupo_mes",
        "go_distribuicao_cobertura_mes",
        "go_distribuicao_financiamento_mes",
    ]:
        conn.execute(f'DROP VIEW IF EXISTS "{v}";')

    # ============================
    # GO 1) Total do setor por mês
    # ============================
    conn.execute("""
        CREATE VIEW go_benef_total_mes AS
        SELECT
            competencia,
            SUM(beneficiarios) AS total_beneficiarios_setor
        FROM si_beneficiarios_operadora
        GROUP BY competencia;
    """)

    # =====================================
    # GO 2) Beneficiários por operadora/mês
    # =====================================
    conn.execute("""
        CREATE VIEW go_benef_por_operadora_mes AS
        SELECT
            competencia,
            registro_ans,
            SUM(beneficiarios) AS beneficiarios
        FROM si_beneficiarios_operadora
        GROUP BY competencia, registro_ans;
    """)

    # ==========================================
    # GO 3) Market share + ranking por mês
    # ==========================================
    conn.execute("""
        CREATE VIEW go_market_share_mes AS
        WITH base AS (
            SELECT
                b.competencia,
                b.registro_ans,
                o.razao_social,
                o.nome_fantasia,
                o.modalidade AS modalidade_operadora,
                o.uf,
                b.beneficiarios
            FROM go_benef_por_operadora_mes b
            LEFT JOIN si_operadora o
              ON o.registro_ans = b.registro_ans
        ),
        setor AS (
            SELECT
                competencia,
                SUM(beneficiarios) AS total_setor
            FROM base
            GROUP BY competencia
        )
        SELECT
            base.competencia,
            base.registro_ans,
            COALESCE(base.razao_social, base.nome_fantasia, 'N/I') AS operadora_nome,
            base.modalidade_operadora,
            base.uf,
            base.beneficiarios,
            setor.total_setor,
            ROUND( (1.0 * base.beneficiarios / setor.total_setor) * 100, 4) AS market_share_pct,
            DENSE_RANK() OVER (
                PARTITION BY base.competencia
                ORDER BY base.beneficiarios DESC
            ) AS rank_mes
        FROM base
        JOIN setor
          ON setor.competencia = base.competencia;
    """)

    # ===================================================
    # GO 4) Top 10 do último mês disponível
    # ===================================================
    conn.execute("""
        CREATE VIEW go_top10_operadoras_ultimo_mes AS
        WITH max_mes AS (
            SELECT MAX(competencia) AS competencia
            FROM si_beneficiarios_operadora
        )
        SELECT
            g.*
        FROM go_market_share_mes g
        JOIN max_mes m
          ON g.competencia = m.competencia
        ORDER BY g.rank_mes
        LIMIT 10;
    """)

    # ===================================================
    # GO 5) Distribuições por dimensões (último mês)
    # ===================================================
    conn.execute("""
        CREATE VIEW go_distribuicao_modalidade_grupo_mes AS
        WITH max_mes AS (SELECT MAX(competencia) AS competencia FROM si_beneficiarios_operadora)
        SELECT
            b.competencia,
            COALESCE(b.modalidade_grupo, 'N/I') AS modalidade_grupo,
            SUM(b.beneficiarios) AS beneficiarios
        FROM si_beneficiarios_operadora b
        JOIN max_mes m ON b.competencia = m.competencia
        GROUP BY b.competencia, COALESCE(b.modalidade_grupo, 'N/I')
        ORDER BY beneficiarios DESC;
    """)

    conn.execute("""
        CREATE VIEW go_distribuicao_contratacao_grupo_mes AS
        WITH max_mes AS (SELECT MAX(competencia) AS competencia FROM si_beneficiarios_operadora)
        SELECT
            b.competencia,
            COALESCE(b.contratacao_grupo, 'N/I') AS contratacao_grupo,
            SUM(b.beneficiarios) AS beneficiarios
        FROM si_beneficiarios_operadora b
        JOIN max_mes m ON b.competencia = m.competencia
        GROUP BY b.competencia, COALESCE(b.contratacao_grupo, 'N/I')
        ORDER BY beneficiarios DESC;
    """)

    conn.execute("""
        CREATE VIEW go_distribuicao_cobertura_mes AS
        WITH max_mes AS (SELECT MAX(competencia) AS competencia FROM si_beneficiarios_operadora)
        SELECT
            b.competencia,
            COALESCE(b.cobertura, 'N/I') AS cobertura,
            SUM(b.beneficiarios) AS beneficiarios
        FROM si_beneficiarios_operadora b
        JOIN max_mes m ON b.competencia = m.competencia
        GROUP BY b.competencia, COALESCE(b.cobertura, 'N/I')
        ORDER BY beneficiarios DESC;
    """)

    conn.execute("""
        CREATE VIEW go_distribuicao_financiamento_mes AS
        WITH max_mes AS (SELECT MAX(competencia) AS competencia FROM si_beneficiarios_operadora)
        SELECT
            b.competencia,
            COALESCE(b.financiamento, 'N/I') AS financiamento,
            SUM(b.beneficiarios) AS beneficiarios
        FROM si_beneficiarios_operadora b
        JOIN max_mes m ON b.competencia = m.competencia
        GROUP BY b.competencia, COALESCE(b.financiamento, 'N/I')
        ORDER BY beneficiarios DESC;
    """)

    conn.commit()
    conn.close()

    print("✅ Gold criada com sucesso (views):")
    print("- go_market_share_mes")
    print("- go_top10_operadoras_ultimo_mes")
    print("- go_distribuicao_*_mes")

if __name__ == "__main__":
    main()