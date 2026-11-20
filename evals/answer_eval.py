"""Cevap doğruluğu değerlendirmesi (LLM-as-judge).

Çalıştırma: uv run --env-file .env python evals/answer_eval.py
"""

import asyncio
import uuid

from google import genai
from google.genai import types
from pydantic import BaseModel

from ai_support_agent.api import ajan_olaylari

# (soru, cevapta bulunması gereken bilgi)
VAKALAR = [
    ("İade süresi kaç gün?", "Ürünler teslimden itibaren 14 gün içinde iade edilebilir."),
    ("Kargo ücreti ne kadar?", "500 TL ve üzeri ücretsiz, altı 49,90 TL."),
    (
        "Açılmış protein tozunu iade edebilir miyim?",
        "Hayır, açılmış takviye ürünleri iade edilemez.",
    ),
    ("SP-1004 nerede?", "Kargoda, takip numarası TRK-558813."),
    ("SP-9999 nerede?", "Böyle bir sipariş bulunamadı; bilgi uydurulmamalı."),
]

BEKLEME_SANIYE = 15
HAKEM_MODELI = "gemini-3.5-flash-lite"


class Karar(BaseModel):
    dogru: bool
    gerekce: str


async def cevap_al(soru: str) -> str:
    """Soruyu yeni bir oturumda sorar ve son cevabı döndürür."""
    cevap = ""
    async for olay, veri in ajan_olaylari("eval", str(uuid.uuid4()), soru):
        if olay == "message":
            cevap = veri["text"]
    return cevap


def hakem(soru: str, beklenen: str, cevap: str) -> Karar:
    """Cevabın beklenen bilgiyle tutarlı olup olmadığına karar verir."""
    client = genai.Client(
        http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=5))
    )
    sonuc = client.models.generate_content(
        model=HAKEM_MODELI,
        contents=(
            f"Soru: {soru}\nBeklenen bilgi: {beklenen}\nAsistanın cevabı: {cevap}\n\n"
            "Asistanın cevabı beklenen bilgiyle çelişmeden doğru bilgiyi veriyor mu?"
        ),
        config=types.GenerateContentConfig(
            system_instruction="Sen titiz bir değerlendiricisin. Sadece JSON döndür.",
            response_mime_type="application/json",
            response_schema=Karar,
            temperature=0,
        ),
    )
    return sonuc.parsed


async def main() -> None:
    # Negatif kontrol: hakem bariz yanlış bir cevabı reddetmeli.
    kontrol = hakem("İade süresi kaç gün?", VAKALAR[0][1], "İade süresi 30 gündür.")
    durum = "✓ hakem yanlışı yakaladı" if not kontrol.dogru else "✗ HAKEM GÜVENİLMEZ"
    print(f"Negatif kontrol: {durum}\n")

    gecen = 0
    for soru, beklenen in VAKALAR:
        await asyncio.sleep(BEKLEME_SANIYE)
        cevap = await cevap_al(soru)
        karar = hakem(soru, beklenen, cevap)
        gecen += karar.dogru
        print(f"{'✓' if karar.dogru else '✗'} {soru}\n    {karar.gerekce}")
    print(f"\nSonuç: {gecen}/{len(VAKALAR)}")


if __name__ == "__main__":
    asyncio.run(main())
