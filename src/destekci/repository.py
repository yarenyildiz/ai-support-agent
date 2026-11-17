import json
from pathlib import Path

from destekci.models import Order


class OrderRepository:
    def __init__(self, path: Path) -> None:
        # GÖREV 1: JSON dosyasını oku, her siparişi Order'a çevir,
        # sonucu self._orders adlı bir listede sakla
        self._orders = [Order(**o) for o in json.load(open(path, encoding="utf-8"))]

    def get_by_id(self, order_id: str) -> Order | None:
        # GÖREV 2: ID'si eşleşen siparişi döndür, bulamazsan None döndür
        for order in self._orders:
            if order.order_id == order_id:
                return order
        return None

    def list_by_customer(self, name: str) -> list[Order]:
        # GÖREV 3: o müşterinin tüm siparişlerini liste olarak döndür
        sepet = []
        for order in self._orders:
            if order.customer_name == name:
                sepet.append(order)
        return sepet
