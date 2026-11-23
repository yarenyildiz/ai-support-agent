import math
import re
from collections import Counter

from google import genai

# Türkçe için basit kök: kelimenin ilk 5 harfi ("iadesi" → "iades", "iade" → "iade").
KOK_UZUNLUGU = 5


def vektore_cevir(metinler: list[str]) -> list[list[float]]:
    """Metin listesini embedding vektörlerine çevirir."""
    client = genai.Client()
    sonuc = client.models.embed_content(model="gemini-embedding-001", contents=metinler)
    return [e.values for e in sonuc.embeddings]


def parcala(metin: str) -> list[str]:
    """Markdown metnini '## ' başlıklarına göre bölümlere ayırır."""
    return metin.split("\n## ")[1:]


def benzerlik(a: list[float], b: list[float]) -> float:
    """İki vektör arasındaki kosinüs benzerliğini hesaplar."""
    carpim = sum(x * y for x, y in zip(a, b, strict=True))
    boy_a = sum(x * x for x in a) ** 0.5
    boy_b = sum(y * y for y in b) ** 0.5
    return carpim / (boy_a * boy_b)


def ara(soru: str, parcalar: list[str], vektorler: list[list[float]], k: int = 2) -> list[str]:
    """Soruya anlamca en yakın k parçayı döndürür."""
    soru_vektoru = vektore_cevir([soru])[0]
    puanlar = [benzerlik(soru_vektoru, v) for v in vektorler]
    sirali = sorted(zip(puanlar, parcalar, strict=True), reverse=True)
    return [parca for _, parca in sirali[:k]]


def kelimeler(metin: str) -> list[str]:
    """Metni BM25 için kelime köklerine ayırır (Türkçe büyük/küçük harf uyumlu)."""
    kucuk = metin.replace("İ", "i").replace("I", "ı").lower()
    return [kelime[:KOK_UZUNLUGU] for kelime in re.findall(r"\w+", kucuk)]


def bm25_puanlari(soru: str, parcalar: list[str], k1: float = 1.5, b: float = 0.75) -> list[float]:
    """Her parça için BM25 anahtar kelime puanını hesaplar."""
    belgeler = [kelimeler(p) for p in parcalar]
    ortalama_uzunluk = sum(len(d) for d in belgeler) / len(belgeler)
    belge_frekansi = Counter(k for d in belgeler for k in set(d))
    soru_kelimeleri = kelimeler(soru)
    puanlar = []
    for belge in belgeler:
        tekrar = Counter(belge)
        puan = 0.0
        for kelime in soru_kelimeleri:
            if kelime not in tekrar:
                continue
            df = belge_frekansi[kelime]
            idf = math.log(1 + (len(belgeler) - df + 0.5) / (df + 0.5))
            tf = tekrar[kelime]
            uzunluk_orani = len(belge) / ortalama_uzunluk
            puan += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * uzunluk_orani))
        puanlar.append(puan)
    return puanlar


def puana_gore_sirala(puanlar: list[float]) -> list[int]:
    """Parça indekslerini puana göre büyükten küçüğe sıralar."""
    return sorted(range(len(puanlar)), key=lambda i: puanlar[i], reverse=True)


def rrf(siralamalar: list[list[int]], k: int = 60) -> list[int]:
    """Reciprocal Rank Fusion: birden fazla sıralamayı tek sıralamada birleştirir."""
    toplam: Counter[int] = Counter()
    for siralama in siralamalar:
        for sira, indeks in enumerate(siralama):
            toplam[indeks] += 1 / (k + sira + 1)
    return sorted(toplam, key=lambda i: toplam[i], reverse=True)


if __name__ == "__main__":
    from pathlib import Path

    metin = Path("data/policies.md").read_text(encoding="utf-8")
    parcalar = parcala(metin)
    vektorler = vektore_cevir(parcalar)
    for soru in ["Gönderim bedeli ne kadar?", "Ürünü geri yollayabilir miyim?"]:
        print("SORU:", soru)
        print("EN YAKIN:", ara(soru, parcalar, vektorler, k=1)[0].splitlines()[0])
