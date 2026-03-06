import sqlite3

conn = sqlite3.connect("database/ans.db")
cur = conn.cursor()

for q in [
    ("si_operadora", "SELECT COUNT(*) FROM si_operadora"),
    ("si_beneficiarios_operadora", "SELECT COUNT(*) FROM si_beneficiarios_operadora"),
    ("amostra_competencia", """
        SELECT competencia, COUNT(*) 
        FROM si_beneficiarios_operadora 
        GROUP BY competencia 
        ORDER BY competencia DESC 
        LIMIT 5
    """),
]:
    print("\n==", q[0], "==")
    cur.execute(q[1])
    rows = cur.fetchall()
    for r in rows:
        print(r)

conn.close()