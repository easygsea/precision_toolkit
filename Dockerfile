# Environment variables
ARG DOTNET_VERSION=6.0
ARG HAPPY_VERSION=0.3.15
ARG HTSLIB_VERSION=1.21
ARG JOBLIB_VERSION=0.14.1
ARG POETRY_VERSION=2.0.1
ARG PSUTIL_VERSION=6.1.1
ARG PYTHON_VERSION=3.11.7
ARG WITTYER_VERSION=0.5.2

# Stage 1: Build witty.er from source
FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION} AS witty_er_builder
ARG WITTYER_VERSION
WORKDIR /opt/witty.er

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/Illumina/witty.er.git . && \
    git checkout tags/v${WITTYER_VERSION} -b v${WITTYER_VERSION}-build && \
    cd Wittyer && \
    dotnet publish . -c Release

# Stage 2: Build custom package via Poetry
FROM python:${PYTHON_VERSION}-slim-bookworm AS clinical_tools_builder
ARG POETRY_VERSION
WORKDIR /app

# Copy application files
COPY README.md pyproject.toml poetry.lock ./
COPY src/ /app/src/

# Install and configure poetry, build project, and set permissions
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir "poetry==${POETRY_VERSION}" && \
    poetry config virtualenvs.create false && \
    poetry build && \
    chmod a+rx /app -R

# Stage 3: Runtime
FROM mgibio/hap.py:v${HAPPY_VERSION}
ARG DOTNET_VERSION
ARG HTSLIB_VERSION
ARG JOBLIB_VERSION
ARG PSUTIL_VERSION
ARG PYTHON_VERSION
WORKDIR /app

# Upgrade python2.7 libraries, uninstall vulnerable packages, update system libraries, and install .NET SDK
RUN pip install --upgrade --no-cache-dir "joblib==${JOBLIB_VERSION}" "psutil==${PSUTIL_VERSION}" && \
    pip uninstall --y bx-python cryptography cvxopt idna lxml numexpr pillow pip py pyxdg pycrypto setuptools && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends  \
    apt-transport-https \
    build-essential \
    libbz2-dev \
    libdb5.3-dev \
    libexpat1-dev \
    libffi-dev \
    libgdbm-dev \
    liblzma-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    software-properties-common \
    wget \
    zlib1g-dev && \
    wget --quiet "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && apt-get install -y --no-install-recommends "dotnet-sdk-${DOTNET_VERSION}" && \
    # Build htslib (dependency for bcftools and samtools)
    wget --quiet "https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xjf "htslib-${HTSLIB_VERSION}.tar.bz2" && \
    cd "htslib-${HTSLIB_VERSION}" && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    # Build bcftools
    wget --quiet "https://github.com/samtools/bcftools/releases/download/${HTSLIB_VERSION}/bcftools-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xjf "bcftools-${HTSLIB_VERSION}.tar.bz2" && \
    cd "bcftools-${HTSLIB_VERSION}" && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    cd ../.. && rm -rf htslib-* samtools-* bcftools-* && \
    # Build samtools
    wget --quiet "https://github.com/samtools/samtools/releases/download/${HTSLIB_VERSION}/samtools-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xjf "samtools-${HTSLIB_VERSION}.tar.bz2" && \
    cd "samtools-${HTSLIB_VERSION}" && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    # Build Python
    wget --quiet "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" && \
    tar -xzf "Python-${PYTHON_VERSION}.tgz" && \
    cd "Python-${PYTHON_VERSION}" && \
    ./configure --enable-optimizations && \
    make -j "$(nproc)" && \
    make install && cd .. && rm -rf "Python-${PYTHON_VERSION}" "Python-${PYTHON_VERSION}.tgz" && \
    apt-get remove --purge -y wget apt-transport-https software-properties-common build-essential && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy binaries and wheel
COPY --from=witty_er_builder /opt/witty.er/Wittyer /witty.er
COPY --from=clinical_tools_builder /app/dist/*.whl .

# Set environment variables
ENV PATH="$PATH:/opt/hap.py/bin:/witty.er/bin:/opt/hap.py/libexec/rtg-tools-install"
ENV PATH="$PATH:/usr/bin"

# Update shebangs, create wrapper script, set python defaults, and install package
RUN find /opt/hap.py/bin -type f -name "*.py" -exec sed -i 's~#!/usr/bin/python~#!/usr/bin/env python2.7~' {} \; && \
    printf '#!/bin/bash\ndotnet /witty.er/bin/Release/net6.0/Wittyer.dll "$@"\n' > /witty.er/bin/witty.er && \
    chmod +x /witty.er/bin/witty.er && \
    update-alternatives --install /usr/bin/python python /usr/local/bin/python3 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3 1 && \
    python -m pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir ./*.whl && \
    python2.7 -m pip install --no-cache-dir bx-python --no-binary bx-python && \
    rm ./*.whl && \
    rm -rf /tmp/*

# CDI-158 fix som.py inconsistency issue
RUN sed -i 's~True,  # pass_only~not args.inc_nonpass, # account for nonpass in truth vcf~' /opt/hap.py/bin/som.py
