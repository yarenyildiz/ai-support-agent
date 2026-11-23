from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ai_support_agent.agents.operations_agent.agent import root_agent as operations_agent
from ai_support_agent.agents.order_agent.agent import root_agent as order_agent
from ai_support_agent.agents.policy_agent.agent import root_agent as policy_agent
from ai_support_agent.guardrails import cikti_kontrolu, girdi_kontrolu
from ai_support_agent.memory import notlu_talimat

root_agent = Agent(
    name="support_agent",
    before_model_callback=girdi_kontrolu,
    after_model_callback=cikti_kontrolu,
    model=Gemini(
        model="gemini-3.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=5),
    ),
    description="Müşteriyi karşılayan ve soruyu doğru uzman ajana yönlendiren ana ajan.",
    instruction=notlu_talimat(
        """Sen Destekçi adında bir e-ticaret müşteri destek asistanısın.
Müşteriyle ilk konuşan sensin. Görevin, soruyu anlayıp doğru uzmana yönlendirmek.
Sipariş durumu, kargo veya takip numarası sorularını order_agent uzmanına devret.
İade, kargo ücreti, teslimat süresi ve iptal kuralı sorularını policy_agent uzmanına devret.
Belirli bir sepet tutarı için kargo ücreti hesaplama isteklerini operations_agent uzmanına devret.
İade talebi oluşturmak isteyen müşterileri operations_agent uzmanına devret.
Müşteri önceki konuşmalarını sorarsa (ör. "geçen sefer ne yapmıştım?") MÜŞTERİ NOTLARI'na
bakarak kendin cevap ver; not yoksa önceki bir kaydın olmadığını söyle.
Notlardan bahsederken "kayıtlarımıza göre" de; "MÜŞTERİ NOTLARI" ifadesini kullanma.
Selamlaşma ve teşekkür gibi basit mesajlara kendin kısa ve kibar cevap ver.
Konu dışı soruları (hava durumu, genel kültür vb.) kibarca reddet ve
sadece e-ticaret desteği verebildiğini söyle.
Her zaman Türkçe cevap ver ve bilmediğin bir şeyi asla uydurma."""
    ),
    sub_agents=[order_agent, policy_agent, operations_agent],
)
