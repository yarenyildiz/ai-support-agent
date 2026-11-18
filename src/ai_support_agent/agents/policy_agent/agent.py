from pathlib import Path

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

POLITIKA_DOSYASI = Path("data/policies.md")


def politikalari_getir() -> str:
    """Mağazanın iade, kargo, teslimat, iptal ve iletişim politikalarını getirir."""
    return POLITIKA_DOSYASI.read_text(encoding="utf-8")


root_agent = Agent(
    name="policy_agent",
    model=Gemini(
        model="gemini-3.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=5),
    ),
    description="İade, kargo, teslimat ve iptal politikası sorularını yanıtlar.",
    instruction="""Sen mağaza politikaları uzmanısın.
Politika sorularında mutlaka politikalari_getir aracını kullan.
Sadece politika metninde yazanlara dayanarak kısa ve Türkçe cevap ver.
Metinde olmayan bir kural uydurma; bilmiyorsan müşteri hizmetlerine yönlendir.""",
    tools=[politikalari_getir],
)
