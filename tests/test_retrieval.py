import os
from functools import cache
from pathlib import Path

import pytest

from ai_support_agent.rag import ara, parcala, vektore_cevir

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY gerekli"
)

ALTIN_KUME = [
    ("Gönderim bedeli ne kadar?", "Kargo"),
    ("Ürünü geri yollayabilir miyim?", "İade"),
    ("Açılmış kremi iade edebilir miyim?", "İade"),
    ("Siparişler kaç günde kargoya veriliyor?", "Teslimat"),
    ("Hafta sonu kargo çıkıyor mu?", "Teslimat"),
    ("Siparişimi vazgeçip iptal edebilir miyim?", "İptal"),
    ("Müşteri hizmetlerine hangi saatlerde ulaşırım?", "İletişim"),
]


@cache
def indeks() -> tuple[list[str], list[list[float]]]:
    parcalar = parcala(Path("data/policies.md").read_text(encoding="utf-8"))
    return parcalar, vektore_cevir(parcalar)


@pytest.mark.parametrize(("soru", "beklenen_bolum"), ALTIN_KUME)
def test_dogru_bolum_ilk_sirada(soru: str, beklenen_bolum: str) -> None:
    parcalar, vektorler = indeks()
    en_yakin = ara(soru, parcalar, vektorler, k=1)[0]
    assert en_yakin.splitlines()[0] == beklenen_bolum
    