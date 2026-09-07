# Optional. CI does not require Docker.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY evals ./evals
COPY tests ./tests

RUN pip install --no-cache-dir -e ".[dev]"

ENTRYPOINT ["ops-agent"]
CMD ["eval"]
