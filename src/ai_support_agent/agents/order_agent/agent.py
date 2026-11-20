from pathlib import Path

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ai_support_agent.guardrails import girdi_kontrolu
from ai_support_agent.repository import OrderRepository

repo = OrderRepository(Path("data/orders.json"))


def siparis_durumu_getir(siparis_no: str) -> dict:
    """Sipariş numarasına göre siparişin durumunu ve kargo bilgisini getirir."""
    siparis = repo.get_by_id(siparis_no)
    if siparis is None:
        return {"hata": "Sipariş bulunamadı"}
    return siparis.model_dump(mode="json")


root_agent = Agent(
    name="order_agent",
    before_model_callback=girdi_kontrolu,
    disallow_transfer_to_peers=True,
    model=Gemini(
        model="gemini-3.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=5),
    ),
    description="Sipariş durumu ve kargo takibi sorularını yanıtlar.",
    instruction="""Sen Destekçi adında bir e-ticaret müşteri destek asistanısın.
Müşterilere kibar, kısa ve Türkçe cevap ver.
Sipariş sorularında mutlaka siparis_durumu_getir aracını kullan.
Bilmediğin bir şeyi asla uydurma.""",
    tools=[siparis_durumu_getir],
)
