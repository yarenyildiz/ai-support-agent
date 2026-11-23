import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ai_support_agent.api import app

client = TestClient(app)


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


def test_anahtar_ayarliysa_eksik_anahtar_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "gizli")
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


def test_ana_sayfa_dokumantasyona_yonlendirir() -> None:
    cevap = client.get("/", follow_redirects=False)
    assert cevap.status_code == 307
    assert cevap.headers["location"] == "/docs"
