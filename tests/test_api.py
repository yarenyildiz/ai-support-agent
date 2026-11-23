import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ai_support_agent import api
from ai_support_agent.api import app
from ai_support_agent.rate_limit import DemoSinirlayici

client = TestClient(app)


@pytest.fixture(autouse=True)
def taze_demo_sayaci(monkeypatch: pytest.MonkeyPatch) -> None:
    """Her test boş demo sayaçlarıyla başlasın."""
    monkeypatch.setattr(api, "demo_sinirlayici", DemoSinirlayici())


def test_eksik_alan_422_doner() -> None:
    cevap = client.post("/chat", json={"user_id": "u1", "session_id": "s1"})
    assert cevap.status_code == 422
    assert cevap.json()["detail"][0]["loc"] == ["body", "message"]


def test_yanlis_tip_422_doner() -> None:
    cevap = client.post("/chat", json={"user_id": "u1", "session_id": "s1", "message": 123})
    assert cevap.status_code == 422


def test_dokumantasyon_iki_ucu_listeler() -> None:
    yollar = client.get("/openapi.json").json()["paths"]
    assert "/chat" in yollar
    assert "/chat/stream" in yollar


def test_saglik_kontrolu() -> None:
    cevap = client.get("/health")
    assert cevap.status_code == 200
    assert cevap.json() == {"status": "ok"}


def test_demo_kapaliyken_eksik_anahtar_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
    monkeypatch.setenv("DEMO_GUNLUK_SINIR", "0")
    cevap = client.post("/chat", json={"user_id": "u1", "session_id": "s1", "message": "selam"})
    assert cevap.status_code == 401


def test_anahtar_ayarliysa_yanlis_anahtar_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
    cevap = client.post(
        "/chat/stream",
        json={"user_id": "u1", "session_id": "s1", "message": "selam"},
        headers={"X-API-Key": "yanlis"},
    )
    assert cevap.status_code == 401


def test_dogru_anahtar_kontrolu_gecer(monkeypatch: pytest.MonkeyPatch) -> None:
    # Doğru anahtarla istek doğrulamaya ulaşır: eksik alan için 422 (401 değil). Model çağrılmaz.
    monkeypatch.setenv("API_KEY", "gizli")
    cevap = client.post("/chat", json={"user_id": "u1"}, headers={"X-API-Key": "gizli"})
    assert cevap.status_code == 422


def test_saglik_kontrolu_anahtarsiz_acik(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
    assert client.get("/health").status_code == 200


def test_websocket_anahtarsiz_reddedilir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
    with pytest.raises(WebSocketDisconnect) as hata, client.websocket_connect("/ws/u1/s1"):
        pass
    assert hata.value.code == 1008


def test_ana_sayfa_sohbet_arayuzunu_dondurur(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arayüz herkese açık; anahtar sadece sohbet isteklerinde gerekiyor.
    monkeypatch.setenv("API_KEY", "gizli")
    cevap = client.get("/")
    assert cevap.status_code == 200
    assert cevap.headers["content-type"].startswith("text/html")
    assert "/chat/stream" in cevap.text


def test_akis_hatasi_olay_olarak_bildirilir(monkeypatch: pytest.MonkeyPatch) -> None:
    async def bozuk_akis(*_args):
        yield "transfer", {"to": "order_agent"}
        raise RuntimeError("model çöktü")

    monkeypatch.setattr(api, "ajan_olaylari", bozuk_akis)
    cevap = client.post("/chat/stream", json={"user_id": "u1", "session_id": "s1", "message": "x"})
    assert cevap.status_code == 200
    assert "event: transfer" in cevap.text
    assert "event: error" in cevap.text


def test_demo_anahtarsiz_istegi_sinira_kadar_gecirir(monkeypatch: pytest.MonkeyPatch) -> None:
    # Eksik alanlı istek: sınırı geçerse 422 (model çağrılmaz), sınır dolunca 429.
    monkeypatch.setenv("API_KEY", "gizli")
    monkeypatch.setenv("DEMO_SAATLIK_SINIR", "2")
    kodlar = [client.post("/chat", json={"user_id": "u1"}).status_code for _ in range(3)]
    assert kodlar == [422, 422, 429]


def test_demo_sinirinda_dogru_anahtar_sinirsiz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
    monkeypatch.setenv("DEMO_SAATLIK_SINIR", "1")
    client.post("/chat", json={"user_id": "u1"})
    cevap = client.post("/chat", json={"user_id": "u1"}, headers={"X-API-Key": "gizli"})
    assert cevap.status_code == 422


def test_demo_istemcileri_adrese_gore_ayirir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
    monkeypatch.setenv("DEMO_SAATLIK_SINIR", "1")
    a = {"X-Forwarded-For": "1.1.1.1"}
    b = {"X-Forwarded-For": "2.2.2.2, 10.0.0.1"}
    assert client.post("/chat", json={}, headers=a).status_code == 422
    assert client.post("/chat", json={}, headers=a).status_code == 429
    assert client.post("/chat", json={}, headers=b).status_code == 422


def test_demo_bilgisi_ortam_degiskenini_yansitir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_SAATLIK_SINIR", "3")
    monkeypatch.setenv("DEMO_GUNLUK_SINIR", "0")
    assert client.get("/demo").json() == {"saatlik": 3, "gunluk": 0}
