# Destek ajanı API'si için konteyner imajı.
FROM python:3.11-slim

# uv'yi resmi imajından kopyala (projedeki sürümle aynı).
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Önce sadece bağımlılıklar: kod değişse bile bu katman önbellekten gelir.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Sonra uygulama kodu ve veri.
COPY src ./src
COPY data/orders.json data/policies.md ./data/
RUN uv sync --frozen --no-dev

# root olmayan kullanıcı; SQLite dosyaları için data/ yazılabilir olmalı.
RUN useradd --create-home app && chown -R app:app /app
USER app

ENV PATH="/app/.venv/bin:$PATH" \
    PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn ai_support_agent.api:app --host 0.0.0.0 --port ${PORT}"]
