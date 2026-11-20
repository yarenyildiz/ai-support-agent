import pytest

from ai_support_agent.guardrails import kart_numarasi_var_mi, kart_numarasini_gizle


@pytest.mark.parametrize(
    "metin",
    [
        "Kartım 4111 1111 1111 1111",
        "4111-1111-1111-1111 ile ödedim",
        "4111111111111111",
    ],
)
def test_kart_numarasini_yakalar(metin: str) -> None:
    assert kart_numarasi_var_mi(metin)


@pytest.mark.parametrize(
    "metin",
    [
        "SP-1004 nerede?",
        "Takip numaram TRK-558813",
        "Telefonum 0532 123 45 67",
        "320 TL'lik sepetim için kargo ne kadar?",
    ],
)
def test_normal_mesajlari_engellemez(metin: str) -> None:
    assert not kart_numarasi_var_mi(metin)


def test_kart_numarasi_maskelenir() -> None:
    sonuc = kart_numarasini_gizle("Kartım 4111 1111 1111 1111 ödeme olmadı")
    assert sonuc == "Kartım [GİZLENDİ] ödeme olmadı"
