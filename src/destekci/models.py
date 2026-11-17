from datetime import date
from typing import Literal

from pydantic import BaseModel

OrderStatus = Literal["hazırlanıyor", "kargoda", "teslim edildi", "iade edildi"]


class Order(BaseModel):
    order_id: str
    customer_name: str
    product: str
    status: OrderStatus
    order_date: date
    cargo_tracking_no: str | None
