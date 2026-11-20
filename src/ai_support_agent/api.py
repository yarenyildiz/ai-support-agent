import json

from fastapi import FastAPI
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


def _sse(olay: str, veri: dict) -> str:
    """Bir SSE mesajı biçimlendirir."""
    return f"event: {olay}\ndata: {json.dumps(veri, ensure_ascii=False)}\n\n"


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Ajanın devretme, araç çağrısı ve cevap olaylarını SSE olarak akıtır."""
    mesaj = types.Content(role="user", parts=[types.Part(text=req.message)])

    async def olaylar():
        async for event in runner.run_async(
            user_id=req.user_id, session_id=req.session_id, new_message=mesaj
        ):
            if event.actions and event.actions.transfer_to_agent:
                yield _sse("transfer", {"to": event.actions.transfer_to_agent})
            for cagri in event.get_function_calls():
                if cagri.name != "transfer_to_agent":
                    yield _sse("tool_call", {"agent": event.author, "tool": cagri.name})
            if event.is_final_response() and event.content and event.content.parts:
                metin = "".join(p.text or "" for p in event.content.parts)
                yield _sse("message", {"agent": event.author, "text": metin})
        yield _sse("done", {})

    return StreamingResponse(olaylar(), media_type="text/event-stream")
