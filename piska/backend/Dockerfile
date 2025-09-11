FROM python:3.11-slim

ENV POETRY_VERSION=1.8.3 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir uvicorn[standard]

COPY pyproject.toml ./
RUN pip install --no-cache-dir .[dev]

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]


