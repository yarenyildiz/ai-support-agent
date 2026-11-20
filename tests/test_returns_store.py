from pathlib import Path

from ai_support_agent.returns_store import IadeDeposu


def test_talep_numarasi_artar(tmp_path: Path) -> None:
    depo = IadeDeposu(tmp_path / "test.db")
    assert depo.ekle("SP-1006", "beden")["talep_no"] == "IADE-0001"
    assert depo.ekle("SP-1007", "renk")["talep_no"] == "IADE-0002"


def test_ayni_siparise_ikinci_talep_reddedilir(tmp_path: Path) -> None:
    depo = IadeDeposu(tmp_path / "test.db")
    depo.ekle("SP-1006", "beden")
    assert "hata" in depo.ekle("SP-1006", "fikrimi değiştirdim")


def test_talepler_yeniden_acilista_korunur(tmp_path: Path) -> None:
    yol = tmp_path / "test.db"
    IadeDeposu(yol).ekle("SP-1006", "beden")
    assert "hata" in IadeDeposu(yol).ekle("SP-1006", "tekrar")
