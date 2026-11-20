import sys

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

from ai_support_agent.guardrails import girdi_kontrolu

operasyon_araclari = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "ai_support_agent.mcp_server"],
        )
    )
)

root_agent = Agent(
    name="operations_agent",
    before_model_callback=girdi_kontrolu,
    disallow_transfer_to_peers=True,
    model=Gemini(
        model="gemini-3.5-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=5),
    ),
    description="Kargo ücreti hesaplama ve iade talebi oluşturma işlemlerini yapar.",
    instruction="""Sen operasyon uzmanısın.
Kargo ücreti hesaplama isteklerinde mutlaka kargo_ucreti_hesapla aracını kullan.
İade talebi oluşturmak için sipariş numarası ve iade sebebi gerekir;
eksikse müşteriden iste, sonra iade_talebi_olustur aracını kullan.
Araç hata dönerse hatayı müşteriye nazikçe açıkla.
Kısa ve Türkçe cevap ver. Sonuçları asla tahmin etme.""",
    tools=[operasyon_araclari],
)
