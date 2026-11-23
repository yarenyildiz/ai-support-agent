from pathlib import Path

from google import genai
from google.genai import types

from ai_support_agent.repository import OrderRepository

repo = OrderRepository(Path("data/orders.json"))


def siparis_durumu_getir(siparis_no: str) -> dict:
    """Sipariş numarasına göre siparişin durumunu ve kargo bilgisini getirir."""
    print(f"  [araç çağrıldı: {siparis_no}]")
    # GÖREV 1: buraya kodunuzu yazın
    siparis = repo.get_by_id(siparis_no)
    if siparis is None:
        return {"hata": "Sipariş bulunamadı"}
    return siparis.model_dump(mode="json")


client = genai.Client(
    http_options=types.HttpOptions(
        timeout=60000,
        retry_options=types.HttpRetryOptions(attempts=5),
    )
)

chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        system_instruction="""Senin adın Nova. Bir e-ticaret şirketinin müşteri destek asistanısın.
Müşterilere kibar, kısa ve Türkçe cevap ver.
Sipariş sorularında mutlaka siparis_durumu_getir aracını kullan.
Bilmediğin bir şeyi asla uydurma.""",
        tools=[siparis_durumu_getir],
    ),
)

print("Nova: Merhaba! Size nasıl yardımcı olabilirim? (Çıkmak için 'çıkış' yazın)")

while True:
    soru = input("Siz: ")
    if soru == "çıkış":
        print("Nova: Görüşmek üzere! 👋")
        break
    cevap = chat.send_message(soru)
    print("Nova:", cevap.text)
