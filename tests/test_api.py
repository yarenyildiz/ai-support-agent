from fastapi.testclient import TestClient

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
