from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from ai_support_agent.agents.order_agent.agent import root_agent as order_agent

root_agent = Agent(
    name="support_agent",
    model=Gemini(
        model="gemini-3.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=5),
    ),
    description="Müşteriyi karşılayan ve soruyu doğru uzman ajana yönlendiren ana ajan.",
    instruction="""Sen Destekçi adında bir e-ticaret müşteri destek asistanısın.
Müşteriyle ilk konuşan sensin. Görevin, soruyu anlayıp doğru uzmana yönlendirmek.
Sipariş durumu, kargo veya takip numarası sorularını order_agent uzmanına devret.
Selamlaşma ve teşekkür gibi basit mesajlara kendin kısa ve kibar cevap ver.
Konu dışı soruları (hava durumu, genel kültür vb.) kibarca reddet ve
sadece e-ticaret desteği verebildiğini söyle.
Her zaman Türkçe cevap ver ve bilmediğin bir şeyi asla uydurma.""",
    sub_agents=[order_agent],
)