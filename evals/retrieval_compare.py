"""Arama yöntemlerini karşılaştırır: vektör, BM25 ve hibrit (RRF).

Her soru için doğru bölümün ilk sırada gelip gelmediğini (hit@1) ölçer.
Çalıştırma: uv run --env-file .env python evals/retrieval_compare.py
"""

from pathlib import Path

from ai_support_agent.rag import (
    benzerlik,
    bm25_puanlari,
    parcala,
    puana_gore_sirala,
    rrf,
    vektore_cevir,
)

# (soru, doğru bölüm). İlk 7 soru tests/test_retrieval.py ile aynı; sonrakiler daha zor.
VAKALAR = [
    ("Gönderim bedeli ne kadar?", "Kargo"),
    ("Ürünü geri yollayabilir miyim?", "İade"),
    ("Açılmış kremi iade edebilir miyim?", "İade"),
    ("Siparişler kaç günde kargoya veriliyor?", "Teslimat"),
    ("Hafta sonu kargo çıkıyor mu?", "Teslimat"),
    ("Siparişimi vazgeçip iptal edebilir miyim?", "İptal"),
    ("Müşteri hizmetlerine hangi saatlerde ulaşırım?", "İletişim"),
    ("49,90 TL ne için alınıyor?", "Kargo"),
    ("Paramı ne zaman geri alırım?", "İade"),
    ("Kusurlu ürünün dönüş masrafını kim karşılar?", "İade"),
    ("Saat 20:00'de birine ulaşabilir miyim?", "İletişim"),
    ("Yoldaki paketi durdurabilir miyim?", "İptal"),
    ("Resmi tatilde paket gönderiyor musunuz?", "Teslimat"),
    ("Takip kodu bana ne zaman gelir?", "Kargo"),
    ("Hijyen ürünü geri alıyor musunuz?", "İade"),
    ("Kaç TL'den sonra gönderim bedava?", "Kargo"),
]

YONTEMLER = ("vektör", "bm25", "hibrit")


def main() -> None:
    parcalar = parcala(Path("data/policies.md").read_text(encoding="utf-8"))
    basliklar = [p.splitlines()[0] for p in parcalar]
    parca_vektorleri = vektore_cevir(parcalar)
    soru_vektorleri = vektore_cevir([soru for soru, _ in VAKALAR])

    dogru = dict.fromkeys(YONTEMLER, 0)
    for (soru, beklenen), soru_vektoru in zip(VAKALAR, soru_vektorleri, strict=True):
        vektor = puana_gore_sirala([benzerlik(soru_vektoru, v) for v in parca_vektorleri])
        bm25 = puana_gore_sirala(bm25_puanlari(soru, parcalar))
        siralamalar = {"vektör": vektor, "bm25": bm25, "hibrit": rrf([vektor, bm25])}

        satir = []
        for ad, siralama in siralamalar.items():
            bulunan = basliklar[siralama[0]]
            dogru[ad] += bulunan == beklenen
            satir.append(f"{ad}:{bulunan}{'' if bulunan == beklenen else ' ✗'}")
        print(f"{soru}  [{beklenen}]\n    " + "  ".join(satir))

    print()
    for ad in YONTEMLER:
        print(f"{ad:7} hit@1 = {dogru[ad]}/{len(VAKALAR)}")


if __name__ == "__main__":
    main()
