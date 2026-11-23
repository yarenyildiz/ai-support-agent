import json
import logging
import os
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from pydantic import BaseModel

from ai_support_agent.agents.support_agent.agent import root_agent
from ai_support_agent.rate_limit import DemoSinirlayici

APP_NAME = "ai_support_agent"
HATA_MESAJI = "Şu an cevap veremiyorum, lütfen biraz sonra tekrar deneyin."

logger = logging.getLogger(__name__)

session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///data/sessions.db")
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
    auto_create_session=True,
)

app = FastAPI(title="AI Support Agent")


def anahtar_gecerli_mi(gelen: str | None) -> bool:
    """API_KEY ayarlıysa gelen anahtar onunla eşleşmeli; ayarlı değilse (yerel) herkes girer."""
    beklenen = os.environ.get("API_KEY")
    if not beklenen:
        return True
    # compare_digest: karşılaştırma süresinden anahtar tahmin edilmesini (timing attack) önler.
    return gelen is not None and secrets.compare_digest(gelen, beklenen)


demo_sinirlayici = DemoSinirlayici()


def _sinir(ad: str, varsayilan: int) -> int:
    """Demo sınırını ortam değişkeninden okur; 0 demo modunu kapatır."""
    return int(os.environ.get(ad, varsayilan))


def _istemci_adresi(request: Request) -> str:
    """Render gibi bir vekil sunucunun arkasında gerçek istemci adresi X-Forwarded-For'dadır."""
    iletilen = request.headers.get("x-forwarded-for")
    if iletilen:
        return iletilen.split(",")[0].strip()
    return request.client.host if request.client else "bilinmiyor"


async def anahtar_kontrolu(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    """Gemini kotasını korur.

    - Doğru anahtar: sınırsız.
    - Anahtar yok: demo modu açıksa saatlik/günlük sınırla izin verilir (aşılırsa 429).
    - Yanlış anahtar ya da demo kapalı: 401.
    """
    x_api_key = x_api_key or None  # boş başlık = anahtar yok
    if anahtar_gecerli_mi(x_api_key):
        return
    saatlik, gunluk = _sinir("DEMO_SAATLIK_SINIR", 5), _sinir("DEMO_GUNLUK_SINIR", 100)
    if x_api_key is not None or saatlik <= 0 or gunluk <= 0:
        raise HTTPException(status_code=401, detail="Geçersiz veya eksik X-API-Key")
    if sebep := demo_sinirlayici.izin_ver(_istemci_adresi(request), saatlik, gunluk):
        raise HTTPException(status_code=429, detail=sebep)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


class ChatResponse(BaseModel):
    agent: str
    reply: str


ARAYUZ = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
async def ana_sayfa() -> FileResponse:
    """Sohbet arayüzü: /chat/stream olaylarını (devretme, araç, cevap) canlı gösterir."""
    return FileResponse(ARAYUZ)


@app.get("/demo")
async def demo_bilgisi() -> dict[str, int]:
    """Arayüzün gösterdiği anahtarsız demo sınırları (0 = demo kapalı)."""
    return {
        "saatlik": _sinir("DEMO_SAATLIK_SINIR", 5),
        "gunluk": _sinir("DEMO_GUNLUK_SINIR", 100),
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Sağlık kontrolü: süreç ayakta mı? Modeli çağırmaz, kota harcamaz."""
    return {"status": "ok"}


@app.post("/chat", dependencies=[Depends(anahtar_kontrolu)])
async def chat(req: ChatRequest) -> ChatResponse:
    """Müşteri mesajını ajana iletir ve son cevabı döndürür."""
    mesaj = types.Content(role="user", parts=[types.Part(text=req.message)])
    agent, cevap = "", ""
    async for event in runner.run_async(
        user_id=req.user_id, session_id=req.session_id, new_message=mesaj
    ):
        if event.is_final_response() and event.content and event.content.parts:
            agent = event.author
            cevap = "".join(p.text or "" for p in event.content.parts)
    return ChatResponse(agent=agent, reply=cevap)


async def ajan_olaylari(
    user_id: str, session_id: str, metin: str
) -> AsyncIterator[tuple[str, dict]]:
    """Ajanı çalıştırır ve müşteriye gösterilecek olayları (tür, veri) olarak verir.

    SSE ve WebSocket uç noktaları aynı olay akışını kullanır; sadece taşıma biçimi farklıdır.
    """
    mesaj = types.Content(role="user", parts=[types.Part(text=metin)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=mesaj):
        if event.actions and event.actions.transfer_to_agent:
            yield "transfer", {"to": event.actions.transfer_to_agent}
        for cagri in event.get_function_calls():
            if cagri.name != "transfer_to_agent":
                yield "tool_call", {"agent": event.author, "tool": cagri.name}
        if event.is_final_response() and event.content and event.content.parts:
            cevap = "".join(p.text or "" for p in event.content.parts)
            yield "message", {"agent": event.author, "text": cevap}
    yield "done", {}


def _sse(olay: str, veri: dict) -> str:
    """Bir SSE mesajı biçimlendirir."""
    return f"event: {olay}\ndata: {json.dumps(veri, ensure_ascii=False)}\n\n"


@app.post("/chat/stream", dependencies=[Depends(anahtar_kontrolu)])
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Ajanın devretme, araç çağrısı ve cevap olaylarını SSE olarak akıtır."""

    async def akis() -> AsyncIterator[str]:
        try:
            async for olay, veri in ajan_olaylari(req.user_id, req.session_id, req.message):
                yield _sse(olay, veri)
        except Exception:
            # Akış başladıktan sonra HTTP durum kodu değiştirilemez; hatayı bir olay olarak bildir.
            logger.exception("Ajan akışı başarısız oldu")
            yield _sse("error", {"message": HATA_MESAJI})

    return StreamingResponse(akis(), media_type="text/event-stream")


@app.websocket("/ws/{user_id}/{session_id}")
async def chat_ws(websocket: WebSocket, user_id: str, session_id: str) -> None:
    """Açık bağlantı üzerinden çok turlu sohbet: her metin mesajı bir tur başlatır.

    Tarayıcılar WebSocket'e başlık ekleyemediği için anahtar ?api_key= ile gelir.
    """
    if not anahtar_gecerli_mi(websocket.query_params.get("api_key")):
        await websocket.close(code=1008)  # 1008 = policy violation
        return
    await websocket.accept()
    try:
        while True:
            metin = await websocket.receive_text()
            async for olay, veri in ajan_olaylari(user_id, session_id, metin):
                await websocket.send_json({"type": olay, **veri})
    except WebSocketDisconnect:
        pass
