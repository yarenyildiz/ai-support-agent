import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from ai_support_agent.agents.support_agent.agent import root_agent

APP_NAME = "ai_support_agent"

session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
    auto_create_session=True,
)

app = FastAPI(title="AI Support Agent")


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


class ChatResponse(BaseModel):
    agent: str
    reply: str


@app.post("/chat")
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


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Ajanın devretme, araç çağrısı ve cevap olaylarını SSE olarak akıtır."""

    async def akis() -> AsyncIterator[str]:
        async for olay, veri in ajan_olaylari(req.user_id, req.session_id, req.message):
            yield _sse(olay, veri)

    return StreamingResponse(akis(), media_type="text/event-stream")


@app.websocket("/ws/{user_id}/{session_id}")
async def chat_ws(websocket: WebSocket, user_id: str, session_id: str) -> None:
    """Açık bağlantı üzerinden çok turlu sohbet: her metin mesajı bir tur başlatır."""
    await websocket.accept()
    try:
        while True:
            metin = await websocket.receive_text()
            async for olay, veri in ajan_olaylari(user_id, session_id, metin):
                await websocket.send_json({"type": olay, **veri})
    except WebSocketDisconnect:
        pass
