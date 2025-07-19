FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY uv.lock .
COPY govee_temperature/ govee_temperature/

# Sync dependencies
RUN uv sync --frozen

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["uv", "run", "govee-temperature"]