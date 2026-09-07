import sqlite3
from datetime import datetime
from typing import List, Dict, Any

DATABASE = "database.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS shits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shit VARCHAR(100) NOT NULL,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_shit_record(shit_text: str) -> Dict[str, Any]:
    """Adiciona um novo registro de palavrão no banco de dados."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        "INSERT INTO shits (shit, datetime) VALUES (?, ?)",
        (shit_text, datetime.now())
    )
    conn.commit()

    record_id = cursor.lastrowid
    conn.close()

    return {
        "id": record_id,
        "shit": shit_text,
        "datetime": datetime.now()
    }


def get_today_count() -> int:
    """Retorna a contagem de palavrões registrados hoje."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.execute(
        "SELECT COUNT(*) as count FROM shits WHERE date(datetime) = ?",
        (today,)
    )
    result = cursor.fetchone()
    conn.close()

    return result["count"] if result else 0


def get_all_records() -> List[Dict[str, Any]]:
    """Retorna todos os registros (para debug/futuro)."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("SELECT * FROM shits ORDER BY datetime DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso!")
