FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv pip install --no-cache -r pyproject.toml

COPY . .

# Copy entrypoint scripts and make them executable
RUN chmod +x /app/entrypoint-dev.sh /app/entrypoint-prod.sh

EXPOSE 8000

CMD ["/app/entrypoint-prod.sh"]