FROM python:3.11.7-slim-bookworm

# Prepare for manual installation of vulnerable dependencies
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
ENV ZLIB_VERSION 1.3.1

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential wget libexpat1 libexpat1-dev libkrb5-dev zlib1g bash && \
    # Download and build the latest zlib
    wget https://zlib.net/zlib-${ZLIB_VERSION}.tar.gz && \
    tar -xzf zlib-${ZLIB_VERSION}.tar.gz && cd zlib-${ZLIB_VERSION} && \
    ./configure && make && make install && \
    cp zlib.h zconf.h /usr/local/include && chmod 644 /usr/local/include/zlib.h /usr/local/include/zconf.h && \
    cd .. && rm -rf zlib-${ZLIB_VERSION} zlib-${ZLIB_VERSION}.tar.gz && \
    # Clean up build tools and unnecessary files
    apt-get remove -y build-essential wget && apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install poetry
RUN pip install --upgrade pip && pip install --no-cache-dir poetry

# Create and set working directory
WORKDIR /app

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Intall Python dependencies
COPY README.md pyproject.toml ./
RUN poetry install --only main --no-root --no-ansi

# Copy the rest of the application code
COPY src/ /app/src/

# Set non-root user
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
