import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

KART_DESENI = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
GIZLI = "[GİZLENDİ]"


def kart_numarasi_var_mi(metin: str) -> bool:
    """Metinde kredi kartı numarasına benzeyen bir dizi olup olmadığını kontrol eder."""
    return KART_DESENI.search(metin) is not None


def kart_numarasini_gizle(metin: str) -> str:
    """Metindeki kart numaralarını maskeler."""
    return KART_DESENI.sub(GIZLI, metin)


def girdi_kontrolu(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """Model çağrısından önce tüm geçmişteki kart numaralarını maskeler.

    Kart numarası son mesajdaysa modeli hiç çağırmadan uyarı döndürür.
    """
    son_mesajda_var = False
    for sira, icerik in enumerate(llm_request.contents):
        for parca in icerik.parts or []:
            if parca.text and kart_numarasi_var_mi(parca.text):
                parca.text = kart_numarasini_gizle(parca.text)
                if sira == len(llm_request.contents) - 1:
                    son_mesajda_var = True

    if son_mesajda_var:
        uyari = (
            "Güvenliğiniz için kart numaranızı sohbete yazmayın; "
            "numaranızı yapay zekâ modeline göndermedim. Size başka nasıl yardımcı olabilirim?"
        )
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=uyari)]))
    return None
