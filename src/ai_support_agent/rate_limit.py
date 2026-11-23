"""Anahtarsız demo kullanımı için basit hız sınırlayıcı.

Sayaçlar süreç hafızasında tutulur: sunucu yeniden başlayınca sıfırlanır ve birden fazla
sunucu kopyası arasında paylaşılmaz. Kota korumasına yeter; kesin sınır için Redis gerekir.
"""

import time
from collections import deque
from datetime import UTC, datetime

SAAT = 3600.0


class DemoSinirlayici:
    """İstemci başına saatlik (kayan pencere) ve tüm demo için günlük istek sınırı."""

    def __init__(self) -> None:
        self._istemciler: dict[str, deque[float]] = {}
        self._gun = ""
        self._gunluk_sayac = 0

    def izin_ver(
        self, istemci: str, saatlik: int, gunluk: int, simdi: float | None = None
    ) -> str | None:
        """İstek demo sınırları içindeyse sayar ve None döndürür; değilse sebebini döndürür."""
        simdi = time.time() if simdi is None else simdi
        gun = datetime.fromtimestamp(simdi, UTC).date().isoformat()
        if gun != self._gun:
            self._gun, self._gunluk_sayac = gun, 0

        zamanlar = self._istemciler.setdefault(istemci, deque())
        while zamanlar and simdi - zamanlar[0] >= SAAT:
            zamanlar.popleft()

        if self._gunluk_sayac >= gunluk:
            return "Bugünkü demo kotası doldu. Yarın tekrar deneyin."
        if len(zamanlar) >= saatlik:
            return f"Demo sınırı: saatte {saatlik} mesaj. Biraz sonra tekrar deneyin."

        zamanlar.append(simdi)
        self._gunluk_sayac += 1
        self._temizle(simdi)
        return None

    def _temizle(self, simdi: float) -> None:
        """Bir saattir istek atmamış istemcileri unutur (hafıza sınırsız büyümesin)."""
        if len(self._istemciler) > 10_000:
            self._istemciler = {
                k: v for k, v in self._istemciler.items() if v and simdi - v[-1] < SAAT
            }
