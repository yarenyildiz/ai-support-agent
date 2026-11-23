from pathlib import Path

from ai_support_agent.memory import MusteriHafizasi, _sonucu_ac, not_cikar


def test_notlar_musteriye_ozeldir(tmp_path: Path) -> None:
    hafiza = MusteriHafizasi(tmp_path / "memory.db")
    hafiza.ekle("idil", "SP-1006 için IADE-0001 numaralı iade talebi açtı")
    assert hafiza.son_notlar("idil") == ["SP-1006 için IADE-0001 numaralı iade talebi açtı"]
    assert hafiza.son_notlar("baska_musteri") == []


def test_ayni_not_iki_kez_eklenmez(tmp_path: Path) -> None:
    hafiza = MusteriHafizasi(tmp_path / "memory.db")
    hafiza.ekle("idil", "SP-1006 siparişini sordu")
    hafiza.ekle("idil", "SP-1006 siparişini sordu")
    assert len(hafiza.son_notlar("idil")) == 1


def test_son_notlar_sinirli_ve_eskiden_yeniye(tmp_path: Path) -> None:
    hafiza = MusteriHafizasi(tmp_path / "memory.db")
    for i in range(7):
        hafiza.ekle("idil", f"not {i}")
    assert hafiza.son_notlar("idil", adet=3) == ["not 4", "not 5", "not 6"]


def test_notlar_yeniden_acilista_korunur(tmp_path: Path) -> None:
    yol = tmp_path / "memory.db"
    MusteriHafizasi(yol).ekle("idil", "SP-1006 siparişini sordu")
    assert MusteriHafizasi(yol).son_notlar("idil") == ["SP-1006 siparişini sordu"]


def test_mcp_yaniti_acilir() -> None:
    yanit = {"content": [{"type": "text", "text": '{"talep_no": "IADE-0001"}'}], "isError": False}
    assert _sonucu_ac(yanit) == {"talep_no": "IADE-0001"}


def test_sozluk_olmayan_yanit_bos_doner() -> None:
    assert _sonucu_ac(None) == {}


def test_basarili_iade_not_uretir() -> None:
    sonuc = {"talep_no": "IADE-0002", "siparis_no": "SP-1006", "sebep": "beden"}
    assert not_cikar("iade_talebi_olustur", sonuc) == (
        "SP-1006 için IADE-0002 numaralı iade talebi açtı (sebep: beden)"
    )


def test_hatali_sonuc_not_uretmez() -> None:
    assert not_cikar("iade_talebi_olustur", {"hata": "Sipariş bulunamadı"}) is None
    assert not_cikar("politika_ara", {"metin": "..."}) is None
