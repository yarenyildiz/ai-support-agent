from functools import cache
from pathlib import Path

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ai_support_agent.guardrails import girdi_kontrolu
from ai_support_agent.rag import ara, parcala, vektore_cevir

POLITIKA_DOSYASI = Path("data/policies.md")


@cache
def _indeks() -> tuple[list[str], list[list[float]]]:
    """Politika belgesini parçalar ve vektörlerini bir kez hesaplar."""
    parcalar = parcala(POLITIKA_DOSYASI.read_text(encoding="utf-8"))
    return parcalar, vektore_cevir(parcalar)


def politika_ara(soru: str) -> str:
    """Müşterinin sorusuyla ilgili mağaza politikası bölümlerini bulur."""
    parcalar, vektorler = _indeks()
    return "\n\n".join(ara(soru, parcalar, vektorler, k=2))


root_agent = Agent(
    name="policy_agent",
    before_model_callback=girdi_kontrolu,
    model=Gemini(
        model="gemini-3.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=5),
    ),
    description="İade, kargo, teslimat ve iptal politikası sorularını yanıtlar.",
    instruction="""Sen mağaza politikaları uzmanısın.
Politika sorularında mutlaka politika_ara aracını, müşterinin sorusuyla çağır.
Sadece aracın döndürdüğü metne dayanarak kısa ve Türkçe cevap ver.
Metinde olmayan bir kural uydurma; bilmiyorsan müşteri hizmetlerine yönlendir.
Cevabın sonuna, kullandığın bölümün başlığını (Kaynak: <başlık>) şeklinde yaz.""",
    tools=[politika_ara],
)
