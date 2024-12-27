FROM python:3.11.7-slim-bullseye

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

# Build the project
RUN poetry build

# Adjust permissions so files are readable by the user running the container
RUN chmod a+rx /app -R
