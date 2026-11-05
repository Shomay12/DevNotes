FROM python:3.12-slim

# Install Node.js for JavaScript execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged sandbox user
RUN useradd -m -s /bin/bash sandboxuser

WORKDIR /sandbox
COPY runner.py /sandbox/runner.py

USER sandboxuser

ENTRYPOINT ["python", "/sandbox/runner.py"]
