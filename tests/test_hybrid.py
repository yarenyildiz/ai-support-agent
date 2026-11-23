from ai_support_agent.rag import bm25_puanlari, kelimeler, puana_gore_sirala, rrf

PARCALAR = [
    "İade\n- Ürünler 14 gün içinde iade edilebilir.",
    "Kargo\n- 500 TL ve üzeri siparişlerde kargo ücretsizdir. Altında 49,90 TL.",
    "İletişim\n- Müşteri hizmetleri 09:00–18:00 arası hizmet verir.",
]


def test_kelimeler_turkce_ve_kok() -> None:
    assert kelimeler("İADESİ Iğdır") == ["iades", "ığdır"]


def test_bm25_birebir_terimi_one_cikarir() -> None:
    sira = puana_gore_sirala(bm25_puanlari("49,90 TL ne için alınıyor?", PARCALAR))
    assert sira[0] == 1


def test_bm25_eslesme_yoksa_sifir() -> None:
    assert bm25_puanlari("hava durumu", PARCALAR) == [0.0, 0.0, 0.0]


def test_rrf_iki_listede_de_ustte_olani_secer() -> None:
    assert rrf([[0, 1, 2], [1, 0, 2]])[2] == 2
    assert rrf([[1, 0, 2], [1, 2, 0]])[0] == 1
