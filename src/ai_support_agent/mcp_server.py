from mcp.server.mcpserver import MCPServer

mcp = MCPServer("operations")


@mcp.tool()
def kargo_ucreti_hesapla(sepet_tutari: float) -> dict:
    """Sepet tutarına göre kargo ücretini hesaplar (TL)."""
    ucret = 0.0 if sepet_tutari >= 500 else 49.90
    return {"sepet_tutari": sepet_tutari, "kargo_ucreti": ucret}


if __name__ == "__main__":
    mcp.run()
