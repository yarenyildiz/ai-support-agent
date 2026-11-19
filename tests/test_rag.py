from ai_support_agent.rag import parcala

ORNEK = """# Başlık

## İade
- 14 gün içinde iade edilebilir.

## Kargo
- 500 TL üzeri ücretsiz."""


def test_basliklara_gore_boler():
    parcalar = parcala(ORNEK)
    assert len(parcalar) == 2


def test_ana_baslik_atilir():
    parcalar = parcala(ORNEK)
    assert parcalar[0].startswith("İade")
