"""
Histórico de ditados em SQLite, em %LOCALAPPDATA%\\Ditar\\history.db.

sqlite3 é stdlib (empacotado automaticamente). Tudo tolerante a erro: o histórico nunca
pode derrubar o ditado.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Ditar" / "history.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), timeout=5)
    c.execute(
        "CREATE TABLE IF NOT EXISTS dictations "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, text TEXT, app TEXT, model TEXT)"
    )
    return c


def add(text: str, app: str = "", model: str = "") -> None:
    if not text or not text.strip():
        return
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO dictations (ts, text, app, model) VALUES (?, ?, ?, ?)",
                (int(time.time()), text, app, model),
            )
    except Exception:
        pass


def recent(limit: int = 200, query: str = "") -> list[tuple]:
    """Retorna [(ts, text, app), ...] mais novos primeiro; filtra por `query` se dado."""
    try:
        with _conn() as c:
            if query:
                cur = c.execute(
                    "SELECT ts, text, app FROM dictations WHERE text LIKE ? "
                    "ORDER BY id DESC LIMIT ?",
                    (f"%{query}%", limit),
                )
            else:
                cur = c.execute(
                    "SELECT ts, text, app FROM dictations ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            return cur.fetchall()
    except Exception:
        return []
