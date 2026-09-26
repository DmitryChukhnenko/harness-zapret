FROM python:3.12-slim-bookworm
WORKDIR /app
COPY pyproject.toml README.md ./
COPY harness/src ./harness/src
RUN pip install --no-cache-dir '.[dev]'
COPY config ./config
COPY tests ./tests
COPY SPEC.md ./
ENV PYTHONUNBUFFERED=1
CMD ["python", "-c", "import time; time.sleep(10**9)"]
