# Minimal Python 3.11 image with OpenTelemetry instrumentation for the app
# This Dockerfile is separate from the Bedrock agent core image and is used
# for building the ECR image referenced in CI workflows.

FROM python:3.11-slim

# Avoid Python creating .pyc files and ensure stdout/stderr are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (kept minimal); add others if your deps require them
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install project dependencies
# If you prefer src/requirements.txt, change the COPY/RUN lines accordingly
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install OpenTelemetry and common instrumentations
RUN pip install --no-cache-dir \
      opentelemetry-distro \
      opentelemetry-exporter-otlp \
      opentelemetry-instrumentation-requests \
    && opentelemetry-bootstrap -a install

# Copy application code
COPY src/ ./src/

# Set sensible OTEL defaults; override at runtime as needed
ENV OTEL_SERVICE_NAME=web-tools \
    OTEL_TRACES_EXPORTER=otlp \
    OTEL_METRICS_EXPORTER=otlp \
    OTEL_LOGS_EXPORTER=otlp \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# If your server listens on a port, you can document it here
EXPOSE 8000

# Default command runs your server with OpenTelemetry instrumentation.
# Adjust to match how your app starts (e.g., uvicorn, flask, etc.).
CMD ["opentelemetry-instrument", "python", "src/server.py"]
