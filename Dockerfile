FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* ./
RUN uv sync
COPY gunicorn.conf.py .

COPY . .

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
