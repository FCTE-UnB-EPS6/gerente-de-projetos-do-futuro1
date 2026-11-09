# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Aplica as correções de segurança do Debian publicadas depois da imagem base.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 gpf
COPY --from=build /install /usr/local
USER gpf
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "gpf.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
