# Environment variables
ARG DOTNET_VERSION=6.0
ARG HAPPY_VERSION=0.3.15
ARG HTSLIB_VERSION=1.21
ARG PYTHON_VERSION=3.11.7
ARG WITTYER_VERSION=0.5.2

# Stage 1: Build witty.er from source
FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION} AS witty_er_builder
ARG WITTYER_VERSION

# Install additional dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone and build witty.er
WORKDIR /opt/witty.er
RUN git clone https://github.com/Illumina/witty.er.git . && \
    git checkout tags/v${WITTYER_VERSION} -b v${WITTYER_VERSION}-build && \
    cd Wittyer && \
    dotnet publish . -c Release

# Stage 2: Build custom package via Poetry
FROM python:${PYTHON_VERSION}-slim-bookworm AS clinical_tools_builder

# Upgrade pip and install poetry
RUN pip install --upgrade pip && pip install --no-cache-dir poetry

# Create and set working directory
WORKDIR /app

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy application files
COPY README.md pyproject.toml poetry.lock ./
COPY src/ /app/src/

# Build the project
RUN poetry build

# Adjust permissions so files are readable by the user running the container
RUN chmod a+rx /app -R

# Stage 3: Runtime
FROM mgibio/hap.py:v${HAPPY_VERSION}
ARG DOTNET_VERSION
ARG HTSLIB_VERSION
ARG PYTHON_VERSION

# Create and set working directory
WORKDIR /app

# Upgrade python2.7 libraries to available latest
RUN pip install --upgrade joblib==0.14.1 psutil==6.1.1

# Uninstall unused vulnerable libraries in python2.7
RUN pip uninstall --y setuptools pycrypto pillow numexpr lxml cvxopt idna cryptography pyxdg py numexpr pip

# Update libraries for fixed vulnerabilities and install .NET SDK
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y wget apt-transport-https software-properties-common && \
    wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && apt-get install -y dotnet-sdk-${DOTNET_VERSION} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install runtime Python, htslib, samtools and bcftools
RUN apt-get update && apt-get install -y build-essential libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev \
    libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev libffi-dev && \
    wget https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2 && \
    tar -xjf htslib-${HTSLIB_VERSION}.tar.bz2 && \
    cd htslib-${HTSLIB_VERSION} && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    # Build samtools
    wget https://github.com/samtools/samtools/releases/download/${HTSLIB_VERSION}/samtools-${HTSLIB_VERSION}.tar.bz2 && \
    tar -xjf samtools-${HTSLIB_VERSION}.tar.bz2 && \
    cd samtools-${HTSLIB_VERSION} && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    # Build bcftools
    wget https://github.com/samtools/bcftools/releases/download/${HTSLIB_VERSION}/bcftools-${HTSLIB_VERSION}.tar.bz2 && \
    tar -xjf bcftools-${HTSLIB_VERSION}.tar.bz2 && \
    cd bcftools-${HTSLIB_VERSION} && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    cd ../.. && rm -rf htslib-* samtools-* bcftools-* && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar -xzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations && \
    make -j $(nproc) && \
    make install && cd .. && rm -rf Python-${PYTHON_VERSION} Python-${PYTHON_VERSION}.tgz

# Remove libraries unnecessary for runtime
RUN apt-get remove --purge -y wget apt-transport-https software-properties-common build-essential && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy binaries
COPY --from=witty_er_builder /opt/witty.er/Wittyer /witty.er
ENV PATH="$PATH:/opt/hap.py/bin:/witty.er/bin:/opt/hap.py/libexec/rtg-tools-install"

# Update shebangs in all Python scripts in hap.py bin to use python2.7
RUN find /opt/hap.py/bin -type f -name "*.py" -exec sed -i 's~#!/usr/bin/python~#!/usr/bin/env python2.7~' {} \;

# Create a wrapper script for witty.er
RUN echo '#!/bin/bash\ndotnet /witty.er/bin/Release/net6.0/Wittyer.dll "$@"' > /witty.er/bin/witty.er && \
    chmod +x /witty.er/bin/witty.er

# Set python3 as the default python and pip
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python3 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3 1
ENV PATH="$PATH:/usr/bin"

# Install the package and cleanup
COPY --from=clinical_tools_builder /app/dist/*.whl .
RUN python -m pip install --upgrade pip setuptools && pip install *.whl && \
    rm *.whl
RUN rm -rf /tmp/*
