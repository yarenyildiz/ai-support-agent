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


SALDIRI_IFADELERI = (
    "talimatlarını unut",
    "talimatları unut",
    "kuralları unut",
    "ignore previous instructions",
    "ignore all instructions",
    "sistem talimatını",
    "system prompt",
)


def talimat_saldirisi_mi(metin: str) -> bool:
    """Bilinen prompt injection ifadelerini arar (büyük/küçük harf duyarsız)."""
    turkce = metin.replace("İ", "i").replace("I", "ı").lower()
    ingilizce = metin.lower()
    return any(ifade in turkce or ifade in ingilizce for ifade in SALDIRI_IFADELERI)


SIZINTI_IFADELERI = (
    "uzmanına devret",
    "aracını kullan",
    "sen destekçi adında",
    "sen mağaza politikaları uzmanısın",
    "sen operasyon uzmanısın",
)


def talimat_sizintisi_mi(metin: str) -> bool:
    """Model cevabında iç talimat ifadeleri geçiyor mu kontrol eder."""
    turkce = metin.replace("İ", "i").replace("I", "ı").lower()
    return any(ifade in turkce for ifade in SIZINTI_IFADELERI)


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

    son = llm_request.contents[-1] if llm_request.contents else None
    son_metin = " ".join(p.text or "" for p in (son.parts or [])) if son else ""
    if son and son.role == "user" and talimat_saldirisi_mi(son_metin):
        uyari = (
            "Bu isteği yerine getiremiyorum. "
            "Sipariş, iade ve kargo konularında yardımcı olabilirim."
        )
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=uyari)]))

    if son_mesajda_var:
        uyari = (
            "Güvenliğiniz için kart numaranızı sohbete yazmayın; "
            "numaranızı yapay zekâ modeline göndermedim. Size başka nasıl yardımcı olabilirim?"
        )
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=uyari)]))
    return None


def cikti_kontrolu(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    """Model cevabını müşteriye gitmeden önce kontrol eder.

    Talimat sızıntısı varsa cevabı değiştirir; kart numaralarını maskeler.
    """
    if not llm_response.content or not llm_response.content.parts:
        return None
    metin = " ".join(p.text or "" for p in llm_response.content.parts)
    if talimat_sizintisi_mi(metin):
        uyari = "Bu bilgiyi paylaşamıyorum. Sipariş, iade ve kargo konularında yardımcı olabilirim."
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=uyari)]))
    if kart_numarasi_var_mi(metin):
        for parca in llm_response.content.parts:
            if parca.text:
                parca.text = kart_numarasini_gizle(parca.text)
        return llm_response
    return None
