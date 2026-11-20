"""Yönlendirme ve araç kullanımı değerlendirmesi (trajectory eval).

Çalıştırma: uv run --env-file .env python evals/routing_eval.py
"""

import asyncio
import uuid

from ai_support_agent.api import ajan_olaylari

# (soru, beklenen cevaplayan ajan, beklenen araç veya None)
VAKALAR = [
    ("SP-1004 nerede?", "order_agent", "siparis_durumu_getir"),
    ("Kargo ücreti ne kadar?", "policy_agent", "politika_ara"),
    ("İade süresi kaç gün?", "policy_agent", "politika_ara"),
    ("320 TL'lik sepetim için kargo ne kadar tutar?", "operations_agent", "kargo_ucreti_hesapla"),
    (
        "SP-1006 ceketimi iade etmek istiyorum, bedeni küçük",
        "operations_agent",
        "iade_talebi_olustur",
    ),
    ("Hava nasıl?", "support_agent", None),
    ("Siparişler genelde kaç günde kargoya veriliyor?", "policy_agent", "politika_ara"),
]

BEKLEME_SANIYE = 15  # ücretsiz hesap: dakikada 15 model isteği


async def vakayi_calistir(soru: str) -> tuple[str | None, list[str]]:
    """Soruyu yeni bir oturumda çalıştırır; cevaplayan ajanı ve çağrılan araçları döndürür."""
    cevaplayan, araclar = None, []
    async for olay, veri in ajan_olaylari("eval", str(uuid.uuid4()), soru):
        if olay == "tool_call":
            araclar.append(veri["tool"])
        elif olay == "message":
            cevaplayan = veri["agent"]
    return cevaplayan, araclar


async def main() -> None:
    gecen = 0
    for sira, (soru, beklenen_ajan, beklenen_arac) in enumerate(VAKALAR):
        if sira > 0:
            await asyncio.sleep(BEKLEME_SANIYE)
        cevaplayan, araclar = await vakayi_calistir(soru)
        arac_dogru = (beklenen_arac in araclar) if beklenen_arac else not araclar
        basarili = cevaplayan == beklenen_ajan and arac_dogru
        gecen += basarili
        isaret = "✓" if basarili else "✗"
        print(f"{isaret} {soru}\n    → {cevaplayan} {araclar}")
    print(f"\nSonuç: {gecen}/{len(VAKALAR)}")
    if gecen < len(VAKALAR):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
