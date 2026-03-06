import os
import csv
import re
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ans.db")

CADOP_CSV = os.path.join(BASE_DIR, "data", "bronze", "operadoras", "Relatorio_cadop.csv")
BENEF_CSV = os.path.join(BASE_DIR, "data", "bronze", "beneficiarios_operadora", "Beneficiarios_operadora_e_carteira.csv")

BATCH_SIZE = 2000


def ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def sanitize_column(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^\w]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "col"
    if re.match(r"^\d", s):
        s = f"c_{s}"
    return s


def detect_encoding(path: str) -> str:
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                f.read(4096)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detect_delimiter(path: str, encoding: str) -> str:
    # tenta sniff no header + algumas linhas
    with open(path, "r", encoding=encoding, newline="") as f:
        sample = f.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        # fallback: se tiver muito ';' no header, usa ';'
        first_line = sample.splitlines()[0] if sample else ""
        return ";" if first_line.count(";") > first_line.count(",") else ","


def create_table(conn: sqlite3.Connection, table: str, columns: List[str]) -> None:
    cols_sql = ", ".join([f'"{c}" TEXT' for c in columns])
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS "{table}" (
            {cols_sql},
            "_ingested_at" TEXT,
            "_source_file" TEXT,
            "_row_num" INTEGER
        );
    """)
    conn.commit()


def insert_rows(
    conn: sqlite3.Connection,
    table: str,
    columns: List[str],
    rows: List[List[Optional[str]]],
    ingested_at: str,
    source_file: str,
    start_row_num: int
) -> None:
    placeholders = ", ".join(["?"] * (len(columns) + 3))
    colnames = ", ".join([f'"{c}"' for c in columns] + ['"_ingested_at"', '"_source_file"', '"_row_num"'])
    sql = f'INSERT INTO "{table}" ({colnames}) VALUES ({placeholders});'

    payload = []
    row_num = start_row_num
    for r in rows:
        payload.append([*r, ingested_at, source_file, row_num])
        row_num += 1

    conn.executemany(sql, payload)


def load_csv_to_bronze(conn: sqlite3.Connection, csv_path: str, table: str) -> Tuple[int, List[str]]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_path}")

    enc = detect_encoding(csv_path)
    delim = detect_delimiter(csv_path, enc)

    ingested_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    source_file = os.path.basename(csv_path)

    total_rows = 0
    batch = []

    with open(csv_path, "r", encoding=enc, newline="") as f:
        reader = csv.reader(f, delimiter=delim)

        header = next(reader, None)
        if not header:
            raise ValueError(f"CSV sem header: {csv_path}")

        # Se o header veio como 1 coluna e tem ';' dentro, split manual (caso edge)
        if len(header) == 1 and ";" in header[0] and delim != ";":
            header = header[0].split(";")
            delim = ";"

        columns = [sanitize_column(h) for h in header]

        # recria a tabela do zero (Bronze reprodutível)
        conn.execute(f'DROP TABLE IF EXISTS "{table}";')
        create_table(conn, table, columns)

        conn.execute("BEGIN;")
        try:
            row_num = 1
            for row in reader:
                if len(row) < len(columns):
                    row = row + [""] * (len(columns) - len(row))
                elif len(row) > len(columns):
                    row = row[:len(columns)]

                batch.append(row)
                if len(batch) >= BATCH_SIZE:
                    insert_rows(conn, table, columns, batch, ingested_at, source_file, row_num)
                    row_num += len(batch)
                    total_rows += len(batch)
                    batch.clear()

            if batch:
                insert_rows(conn, table, columns, batch, ingested_at, source_file, row_num)
                total_rows += len(batch)
                batch.clear()

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    print(f"[{table}] encoding={enc} delimiter='{delim}'")
    return total_rows, columns


def create_indexes(conn: sqlite3.Connection) -> None:
    def col_exists(table: str, col: str) -> bool:
        cur = conn.execute(f'PRAGMA table_info("{table}");')
        return any(r[1] == col for r in cur.fetchall())

    if col_exists("br_benef_operadora_carteira", "cd_operadora"):
        conn.execute('CREATE INDEX IF NOT EXISTS idx_br_benef_cd_operadora ON br_benef_operadora_carteira(cd_operadora);')
    if col_exists("br_benef_operadora_carteira", "id_cmpt"):
        conn.execute('CREATE INDEX IF NOT EXISTS idx_br_benef_id_cmpt ON br_benef_operadora_carteira(id_cmpt);')

    # CADOP às vezes vira registro_ans / registro_da_operadora / etc. (vamos indexar se existir)
    for cand in ["registro_ans", "registro", "reg_ans"]:
        if col_exists("br_cadop", cand):
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_br_cadop_{cand} ON br_cadop({cand});')
            break

    conn.commit()


def main() -> None:
    ensure_parent_dir(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    print(f"SQLite: {DB_PATH}")

    print("\n[1/2] Carregando CADOP (Bronze) ...")
    cadop_rows, cadop_cols = load_csv_to_bronze(conn, CADOP_CSV, "br_cadop")
    print(f"OK: br_cadop -> {cadop_rows} linhas | {len(cadop_cols)} colunas")

    print("\n[2/2] Carregando Beneficiários Operadora/Carteira (Bronze) ...")
    benef_rows, benef_cols = load_csv_to_bronze(conn, BENEF_CSV, "br_benef_operadora_carteira")
    print(f"OK: br_benef_operadora_carteira -> {benef_rows} linhas | {len(benef_cols)} colunas")

    print("\nCriando índices básicos ...")
    create_indexes(conn)
    print("OK: índices criados")

    conn.close()
    print("\n✅ Bronze recarregado no SQLite com sucesso.")


if __name__ == "__main__":
    main()