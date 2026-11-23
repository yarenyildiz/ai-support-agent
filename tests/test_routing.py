"""Çok turlu yönlendirme: yeni tur, son konuşan uzmandan değil merkez ajandan başlamalı."""

from google.adk.agents import _agent_router  # ADK'nın "sıradaki turu kim cevaplar" mantığı
from google.adk.events import Event
from google.adk.sessions import Session
from google.genai import types

from ai_support_agent.agents.support_agent.agent import root_agent


def _cevap(ajan: str) -> Event:
    return Event(
        invocation_id="i1",
        author=ajan,
        content=types.Content(role="model", parts=[types.Part(text="cevap")]),
    )


def test_uzman_cevapladiktan_sonra_yeni_tur_merkezden_baslar() -> None:
    for uzman in ("order_agent", "policy_agent", "operations_agent"):
        oturum = Session(id="s1", app_name="a", user_id="u1", events=[_cevap(uzman)])
        siradaki = _agent_router.find_agent_to_run(
            session=oturum, root_agent=root_agent, resumability_config=None
        )
        assert siradaki.name == "support_agent", uzman
