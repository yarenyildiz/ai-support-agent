from google import genai


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


if __name__ == "__main__":
    from pathlib import Path

    metin = Path("data/policies.md").read_text(encoding="utf-8")
    parcalar = parcala(metin)
    vektorler = vektore_cevir(parcalar)
    for soru in ["Gönderim bedeli ne kadar?", "Ürünü geri yollayabilir miyim?"]:
        print("SORU:", soru)
        print("EN YAKIN:", ara(soru, parcalar, vektorler, k=1)[0].splitlines()[0])
