"""Her model çağrısının token kullanımını ve önbellekten gelen kısmını ölçer.

Context caching'e karar vermek için: istem (prompt) ne kadar büyük, ne kadarı önbellekten geliyor?
Çalıştırma: uv run --env-file .env python evals/token_usage.py
"""

import asyncio
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ai_support_agent.agents.support_agent.agent import root_agent

# Gemini 3 modellerinde önbelleğe alınabilecek en küçük ön ek (Google ve ADK dokümantasyonu).
ONBELLEK_ESIGI = 4096

TURLAR = [
    "SP-1004 nerede?",
    "Peki bunu iade edebilir miyim?",
    "Kargo ücreti ne kadar?",
    "320 TL'lik sepetim için kargo ne kadar tutar?",
]


async def main() -> None:
    runner = Runner(
        app_name="token_olcumu",
        agent=root_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )
    kullanici, oturum = f"olcum-{uuid.uuid4().hex[:6]}", "s1"
    toplam_istem = toplam_onbellek = cagri = 0
    en_buyuk = 0

    for tur, metin in enumerate(TURLAR, start=1):
        if tur > 1:
            await asyncio.sleep(15)  # ücretsiz katman: dakikada 15 istek
        print(f"\nTur {tur}: {metin}")
        mesaj = types.Content(role="user", parts=[types.Part(text=metin)])
        async for event in runner.run_async(
            user_id=kullanici, session_id=oturum, new_message=mesaj
        ):
            kullanim = event.usage_metadata
            if not kullanim or event.partial:
                continue
            istem = kullanim.prompt_token_count or 0
            onbellek = kullanim.cached_content_token_count or 0
            cagri += 1
            toplam_istem += istem
            toplam_onbellek += onbellek
            en_buyuk = max(en_buyuk, istem)
            print(f"    {event.author:17} istem={istem:5}  önbellekten={onbellek:5}")

    oran = toplam_onbellek / toplam_istem if toplam_istem else 0
    print(f"\n{cagri} model çağrısı, toplam istem {toplam_istem} token")
    print(f"Önbellekten gelen: {toplam_onbellek} token (%{oran * 100:.0f})")
    print(f"En büyük istem: {en_buyuk} token (önbellek eşiği {ONBELLEK_ESIGI})")


if __name__ == "__main__":
    asyncio.run(main())
