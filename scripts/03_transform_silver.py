import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ans.db")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # ============================
    # SILVER: si_operadora (CADOP)
    # ============================
    conn.execute("DROP TABLE IF EXISTS si_operadora;")

    conn.execute("""
        CREATE TABLE si_operadora AS
        SELECT
            TRIM(registro_operadora) AS registro_ans,
            TRIM(cnpj) AS cnpj,
            TRIM(razao_social) AS razao_social,
            TRIM(nome_fantasia) AS nome_fantasia,
            TRIM(modalidade) AS modalidade,
            TRIM(cidade) AS cidade,
            TRIM(uf) AS uf,
            TRIM(regiao_de_comercializacao) AS regiao_de_comercializacao,
            TRIM(data_registro_ans) AS data_registro_ans,
            _ingested_at AS ingested_at,
            _source_file AS source_file
        FROM br_cadop
        WHERE TRIM(registro_operadora) IS NOT NULL
          AND TRIM(registro_operadora) <> '';
    """)

    conn.execute("""CREATE INDEX IF NOT EXISTS idx_si_operadora_registro_ans ON si_operadora(registro_ans);""")

    # ======================================
    # SILVER: si_beneficiarios_operadora
    # ======================================
    conn.execute("DROP TABLE IF EXISTS si_beneficiarios_operadora;")

    # id_cmpt pode vir como YYYYMM -> vamos padronizar para YYYY-MM-01
    conn.execute("""
        CREATE TABLE si_beneficiarios_operadora AS
        SELECT
            TRIM(cd_operadora) AS registro_ans,
            CASE
                WHEN LENGTH(TRIM(id_cmpt)) = 6 AND TRIM(id_cmpt) GLOB '[0-9][0-9][0-9][0-9][0-9][0-9]'
                    THEN substr(TRIM(id_cmpt),1,4) || '-' || substr(TRIM(id_cmpt),5,2) || '-01'
                WHEN LENGTH(TRIM(id_cmpt)) = 7 AND substr(TRIM(id_cmpt),5,1) = '-'
                    THEN TRIM(id_cmpt) || '-01'
                WHEN LENGTH(TRIM(id_cmpt)) = 10
                    THEN TRIM(id_cmpt)
                ELSE NULL
            END AS competencia,
            CAST(TRIM(nr_benef) AS INTEGER) AS beneficiarios,
            TRIM(gr_modalidade) AS modalidade_grupo,
            TRIM(gr_contratacao) AS contratacao_grupo,
            TRIM(cobertura) AS cobertura,
            TRIM(tipo_financiamento) AS financiamento,
            TRIM(vigencia_plano) AS vigencia_plano,
            _ingested_at AS ingested_at,
            _source_file AS source_file
        FROM br_benef_operadora_carteira
        WHERE TRIM(cd_operadora) IS NOT NULL
          AND TRIM(cd_operadora) <> '';
    """)

    # Remove registros inválidos
    conn.execute("""
        DELETE FROM si_beneficiarios_operadora
        WHERE competencia IS NULL
           OR beneficiarios IS NULL;
    """)

    # Índices para performance
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_si_benef_registro_ans ON si_beneficiarios_operadora(registro_ans);""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_si_benef_competencia ON si_beneficiarios_operadora(competencia);""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_si_benef_comp_reg ON si_beneficiarios_operadora(competencia, registro_ans);""")

    conn.commit()
    conn.close()

    print("✅ Silver criada com sucesso:")
    print("- si_operadora (chave: registro_ans)")
    print("- si_beneficiarios_operadora (competencia padronizada)")

if __name__ == "__main__":
    main()