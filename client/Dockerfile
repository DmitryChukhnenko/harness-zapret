FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends curl iproute2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY harness/src ./harness/src
RUN pip install --no-cache-dir .
COPY config ./config
COPY client/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["sh", "/entrypoint.sh"]
