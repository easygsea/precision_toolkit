# Stage 1: Build Stage
FROM python:3.11.7-slim-bookworm AS build

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential \
    zlib1g-dev \
    bash \
    curl \
    git && \
    pip install --upgrade pip && \
    pip install --no-cache-dir poetry && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Intall Python dependencies
COPY README.md pyproject.toml ./
RUN poetry install --only main --no-root --no-ansi

# Copy the rest of the application code
COPY src/ /app/src/

# Stage 2: Runtime Stage
FROM python:3.11.7-slim-bookworm

# Copy required runtime dependencies from the build stage
COPY --from=build /app /app

# Set non-root user and working directory
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
WORKDIR /app
