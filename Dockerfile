# Stage 1: Build package via Poetry
FROM python:3.11.7-slim-bookworm AS build

# Upgrade pip and install poetry
RUN pip install --upgrade pip && pip install --no-cache-dir poetry

# Create and set working directory
WORKDIR /app

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install package dependencies
COPY README.md pyproject.toml ./
RUN poetry install --only main --no-root --no-ansi

# Copy the rest of the application code
COPY src/ /app/src/

# Build the project
RUN poetry build

# Adjust permissions so files are readable by the user running the container
RUN chmod a+rx /app -R

# Stage 2: Fix system dependency vulnerabilities and build package via wheel
FROM python:3.11.7-slim-bookworm
ENV ZLIB_VERSION 1.3.1
ENV DEBIAN_FRONTEND=noninteractive

# Create and set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential wget libexpat1 libkrb5-dev zlib1g bash && \
    # Download and build the critical-vulnerability-fixed zlib
    wget https://zlib.net/zlib-${ZLIB_VERSION}.tar.gz && \
    tar -xzf zlib-${ZLIB_VERSION}.tar.gz && cd zlib-${ZLIB_VERSION} && \
    ./configure && make && make install && \
    cd .. && rm -rf zlib-${ZLIB_VERSION} zlib-${ZLIB_VERSION}.tar.gz && \
    # Clean up build tools and unnecessary files
    apt-get remove -y build-essential wget && apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the package and cleanup
COPY --from=build /app/dist/*.whl .
RUN pip install --upgrade pip && pip install *.whl && \
    rm *.whl

# Set non-root user
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
