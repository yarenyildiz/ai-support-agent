from pathlib import Path

from google.adk.sessions import DatabaseSessionService


async def test_oturum_yeniden_acilista_korunur(tmp_path: Path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'sessions.db'}"

    ilk = DatabaseSessionService(db_url=url)
    await ilk.create_session(
        app_name="test", user_id="u1", session_id="s1", state={"not": "SP-1004"}
    )

    yeni = DatabaseSessionService(db_url=url)
    oturum = await yeni.get_session(app_name="test", user_id="u1", session_id="s1")

    assert oturum is not None
    assert oturum.state["not"] == "SP-1004"
