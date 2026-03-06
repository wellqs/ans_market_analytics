import sqlite3

conn = sqlite3.connect("database/ans.db")
cursor = conn.cursor()

def show_columns(table):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    
    print(f"\nColunas da tabela {table}:\n")
    
    for col in cols:
        print(col[1])

show_columns("br_benef_operadora_carteira")
show_columns("br_cadop")

conn.close()