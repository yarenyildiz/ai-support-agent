from pathlib import Path

from ai_support_agent.repository import OrderRepository

VERI = Path("data/orders.json")


def test_var_olan_siparisi_bulur():
    repo = OrderRepository(VERI)

    siparis = repo.get_by_id("SP-1003")

    assert siparis is not None
    assert siparis.customer_name == "Yigit Yalcin"


def test_olmayan_siparis_none_doner():
    repo = OrderRepository(VERI)

    siparis = repo.get_by_id("SP-9999")

    assert siparis is None


def test_musterinin_tum_siparislerini_bulur():
    repo = OrderRepository(VERI)

    siparisler = repo.list_by_customer("İdil Gönder")
    assert len(siparisler) == 2
