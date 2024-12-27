# Stage 1: Build Stage
FROM python:3.11.7-slim-bookworm AS build

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential \
    libexpat1 libexpat1-dev \
    libkrb5-dev \
    wget \
    bash \
    git && \
    wget https://zlib.net/zlib-1.3.1.tar.gz && \
    tar -xzf zlib-1.3.1.tar.gz && cd zlib-1.3.1 && \
    ./configure && make && make install && \
    cd .. && rm -rf zlib-1.3 zlib-1.3.tar.gz && \
    wget https://www.cpan.org/src/5.0/perl-5.40.0.tar.gz && \
    tar -xzf perl-5.40.0.tar.gz && cd perl-5.40.0 && \
    ./Configure -des -Dprefix=/usr/local && \
    make && make install && \
    cd .. && rm -rf perl-5.40.0 perl-5.40.0.tar.gz && \
    pip install --upgrade pip && \
    pip install --no-cache-dir poetry && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for installed binaries
ENV PATH="/usr/local/bin:$PATH"

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
COPY --from=build /usr/local /usr/local
COPY --from=build /app /app

# Set non-root user and working directory
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
WORKDIR /app
