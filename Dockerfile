# Environment variables
ARG DOTNET_VERSION=6.0
ARG PYTHON_VERSION=3.11.7
ARG WITTYER_VERSION=0.5.2

# Stage 1: Use the official biocontainers hap.py image
FROM quay.io/biocontainers/hap.py:0.3.15--py27hcb73b3d_0 AS hap_py

# Upgrade python2.7 packages to available latest
RUN pip install --upgrade numpy==1.16.6 scipy==1.2.3

# Uninstall vulnerable packages in python2.7
RUN pip uninstall --y certifi setuptools pip

# Stage 2: Build witty.er from source
FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION} AS witty_er_builder
ARG WITTYER_VERSION=0.5.2

# Install additional dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone and build witty.er
WORKDIR /opt/witty.er
RUN git clone https://github.com/Illumina/witty.er.git . && \
    git checkout tags/v${WITTYER_VERSION} -b v${WITTYER_VERSION}-build && \
    cd Wittyer && \
    dotnet publish . -c Release

# Stage 3: Build custom package via Poetry
FROM python:${PYTHON_VERSION}-slim-bookworm AS clinical_tools_builder

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

# Stage 4: Runtime
FROM python:${PYTHON_VERSION}-slim-bookworm
ARG DOTNET_VERSION=6.0

# Create and set working directory
WORKDIR /app

# Update system packages for fixed vulnerabilities and install .NET SDK
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y wget apt-transport-https software-properties-common && \
    wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && apt-get install -y dotnet-sdk-${DOTNET_VERSION}

# Remove packages unnecessary for runtime
RUN apt-get remove --purge -y wget apt-transport-https software-properties-common && \
    apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.7 as the default python and pip
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python3 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3 1
ENV PATH="/usr/bin:$PATH"

# Install the package and cleanup
COPY --from=clinical_tools_builder /app/dist/*.whl .
RUN pip install --upgrade pip setuptools && pip install *.whl && \
    rm *.whl

# Copy binaries
COPY --from=hap_py /usr/local/bin /hap.py/bin
COPY --from=hap_py /usr/local/lib /hap.py/lib
RUN rm -f /hap.py/bin/python
COPY --from=witty_er_builder /opt/witty.er/Wittyer /witty.er
ENV PATH="/hap.py/bin:/witty.er/bin:$PATH"

# Update shebangs in all Python scripts in /hap.py/bin to use Python 2.7
RUN find /hap.py/bin -type f -name "*.py" -exec sed -i 's~#!/usr/bin/env python~#!/usr/bin/env python2.7~' {} \;

# Create a wrapper script for witty.er
RUN echo '#!/bin/bash\ndotnet /witty.er/bin/Release/net6.0/Wittyer.dll "$@"' > /witty.er/bin/witty.er && \
    chmod +x /witty.er/bin/witty.er

# Set non-root user
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
