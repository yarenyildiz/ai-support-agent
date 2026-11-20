from pathlib import Path

from mcp.server.mcpserver import MCPServer

from ai_support_agent.repository import OrderRepository
from ai_support_agent.returns_store import IadeDeposu

repo = OrderRepository(Path("data/orders.json"))
iade_deposu = IadeDeposu(Path("data/returns.db"))
mcp = MCPServer("operations")


@mcp.tool()
def kargo_ucreti_hesapla(sepet_tutari: float) -> dict:
    """Sepet tutarına göre kargo ücretini hesaplar (TL)."""
    ucret = 0.0 if sepet_tutari >= 500 else 49.90
    return {"sepet_tutari": sepet_tutari, "kargo_ucreti": ucret}


@mcp.tool()
def iade_talebi_olustur(siparis_no: str, sebep: str) -> dict:
    """Teslim edilmiş bir sipariş için iade talebi oluşturur."""
    siparis = repo.get_by_id(siparis_no)
    if siparis is None:
        return {"hata": "Sipariş bulunamadı"}
    if siparis.status != "teslim edildi":
        return {
            "hata": f"Sadece teslim edilmiş siparişler iade edilebilir (durum: {siparis.status})"
        }
    return iade_deposu.ekle(siparis_no, sebep)


if __name__ == "__main__":
    mcp.run()
