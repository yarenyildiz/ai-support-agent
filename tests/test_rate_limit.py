from ai_support_agent.rate_limit import SAAT, DemoSinirlayici


def test_saatlik_sinir_kayan_pencereyle_acilir() -> None:
    s = DemoSinirlayici()
    assert s.izin_ver("ip", saatlik=2, gunluk=100, simdi=0) is None
    assert s.izin_ver("ip", saatlik=2, gunluk=100, simdi=10) is None
    assert s.izin_ver("ip", saatlik=2, gunluk=100, simdi=20) is not None
    # İlk istek bir saat önce kaldı: bir hak açıldı.
    assert s.izin_ver("ip", saatlik=2, gunluk=100, simdi=SAAT + 1) is None


def test_gunluk_sinir_tum_istemciler_icin_ortak() -> None:
    s = DemoSinirlayici()
    assert s.izin_ver("a", saatlik=5, gunluk=2, simdi=0) is None
    assert s.izin_ver("b", saatlik=5, gunluk=2, simdi=1) is None
    assert "Bugünkü" in s.izin_ver("c", saatlik=5, gunluk=2, simdi=2)


def test_gunluk_sinir_yeni_gunde_sifirlanir() -> None:
    s = DemoSinirlayici()
    assert s.izin_ver("a", saatlik=5, gunluk=1, simdi=0) is None
    assert s.izin_ver("b", saatlik=5, gunluk=1, simdi=60) is not None
    assert s.izin_ver("b", saatlik=5, gunluk=1, simdi=24 * SAAT) is None


def test_reddedilen_istek_sayilmaz() -> None:
    s = DemoSinirlayici()
    s.izin_ver("a", saatlik=1, gunluk=2, simdi=0)
    s.izin_ver("a", saatlik=1, gunluk=2, simdi=1)  # saatlik sınırda reddedildi
    assert s.izin_ver("b", saatlik=1, gunluk=2, simdi=2) is None  # günlük hak hâlâ var
