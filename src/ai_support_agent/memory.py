"""Müşteri hafızası: farklı oturumlar arasında müşteri hakkındaki kısa notlar.

Notlar modelin yazdığı serbest metinden değil, araçların döndürdüğü gerçek
sonuçlardan kod tarafından üretilir; böylece hafızaya uydurma bilgi girmez.
"""

import json
import logging
import sqlite3
from functools import cache
from pathlib import Path
from typing import Any

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool


class MusteriHafizasi:
    """Müşteri notlarını SQLite veritabanında saklar."""

    def __init__(self, yol: Path) -> None:
        self._yol = yol
        with self._baglan() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS musteri_notlari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    not_metni TEXT NOT NULL,
                    olusturma TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, not_metni)
                )"""
            )

    def _baglan(self) -> sqlite3.Connection:
        return sqlite3.connect(self._yol)

    def ekle(self, user_id: str, not_metni: str) -> None:
        """Notu ekler; aynı müşteri için aynı not ikinci kez eklenmez."""
        with self._baglan() as db:
            db.execute(
                "INSERT OR IGNORE INTO musteri_notlari (user_id, not_metni) VALUES (?, ?)",
                (user_id, not_metni),
            )

    def son_notlar(self, user_id: str, adet: int = 5) -> list[str]:
        """Müşterinin en yeni notlarını eskiden yeniye sıralı döndürür."""
        with self._baglan() as db:
            satirlar = db.execute(
                "SELECT not_metni FROM musteri_notlari WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, adet),
            ).fetchall()
        return [satir[0] for satir in reversed(satirlar)]


logger = logging.getLogger(__name__)


@cache
def hafiza() -> MusteriHafizasi:
    """Uygulamanın hafıza deposu; ilk ihtiyaçta açılır (import sırasında dosya oluşturmaz)."""
    return MusteriHafizasi(Path("data/memory.db"))


def _sonucu_ac(yanit: Any) -> dict[str, Any]:
    """Araç yanıtını düz sözlüğe çevirir.

    Python araçları sözlük döndürür; MCP araçları {"content": [{"text": "<json>"}]}
    biçiminde döner; transfer_to_agent gibi araçlar ise None döndürebilir.
    """
    if not isinstance(yanit, dict):
        return {}
    icerik = yanit.get("content")
    if isinstance(icerik, list) and icerik and isinstance(icerik[0], dict):
        try:
            return json.loads(icerik[0].get("text", ""))
        except json.JSONDecodeError:
            return {}
    return yanit


def not_cikar(arac_adi: str, sonuc: dict[str, Any]) -> str | None:
    """Başarılı bir araç sonucundan müşteri notu üretir; not gerekmiyorsa None."""
    if "hata" in sonuc:
        return None
    if arac_adi == "siparis_durumu_getir" and "order_id" in sonuc:
        return (
            f"{sonuc['order_id']} ({sonuc['product']}) siparişini sordu; durum: {sonuc['status']}"
        )
    if arac_adi == "iade_talebi_olustur" and "talep_no" in sonuc:
        return (
            f"{sonuc['siparis_no']} için {sonuc['talep_no']} numaralı iade talebi açtı "
            f"(sebep: {sonuc['sebep']})"
        )
    return None


def hafizaya_yaz(
    tool: BaseTool, args: dict[str, Any], tool_context: Any, tool_response: Any
) -> None:
    """after_tool_callback: araç sonucundan not çıkarıp müşterinin hafızasına yazar.

    Hafıza yardımcı bir özelliktir; burada oluşan bir hata konuşmayı bozmamalı.
    """
    try:
        not_metni = not_cikar(tool.name, _sonucu_ac(tool_response))
        if not_metni:
            hafiza().ekle(tool_context.user_id, not_metni)
    except Exception:
        logger.exception("Müşteri hafızasına yazılamadı")
    return None


def notlu_talimat(temel: str):
    """Talimatın sonuna müşterinin notlarını ekleyen bir instruction provider döndürür."""

    def saglayici(baglam: ReadonlyContext) -> str:
        notlar = hafiza().son_notlar(baglam.user_id)
        if not notlar:
            return temel
        liste = "\n".join(f"- {n}" for n in notlar)
        return f"{temel}\n\nMÜŞTERİ NOTLARI (önceki konuşmalardan, gerçek kayıtlar):\n{liste}"

    return saglayici
