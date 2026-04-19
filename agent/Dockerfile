# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Install system dependencies
# Node.js and npm are required for running the MCP server via npx
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl (pinned version for better caching and reliability)
ARG KUBECTL_VERSION=v1.29.2
RUN ARCH=$(dpkg --print-architecture) && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

# Set the working directory
WORKDIR /app

# Create a non-root user and group
RUN groupadd -r app && useradd -m -r -g app app && mkdir -p /home/app/.kube && chown -R app:app /home/app/.kube

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set ownership to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app

# Expose the API port
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
