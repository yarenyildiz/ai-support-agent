import sqlite3
from pathlib import Path


class IadeDeposu:
    """İade taleplerini SQLite veritabanında saklar."""

    def __init__(self, yol: Path) -> None:
        self._yol = yol
        with self._baglan() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS iade_talepleri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    siparis_no TEXT NOT NULL UNIQUE,
                    sebep TEXT NOT NULL,
                    olusturma TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def _baglan(self) -> sqlite3.Connection:
        return sqlite3.connect(self._yol)

    def ekle(self, siparis_no: str, sebep: str) -> dict:
        """Yeni talep ekler; aynı sipariş için ikinci talepte hata döndürür."""
        try:
            with self._baglan() as db:
                imlec = db.execute(
                    "INSERT INTO iade_talepleri (siparis_no, sebep) VALUES (?, ?)",
                    (siparis_no, sebep),
                )
        except sqlite3.IntegrityError:
            return {"hata": f"{siparis_no} için zaten bir iade talebi var"}
        return {"talep_no": f"IADE-{imlec.lastrowid:04d}", "siparis_no": siparis_no, "sebep": sebep}
