# Environment variables
ARG BEDOPS_VERSION=2.4.41
ARG BEDTOOLS_VERSION=2.31.0
ARG D2_VERSION=0.7.0
ARG DOTNET_VERSION=10.0
ARG HAPPY_VERSION=0.3.15
ARG HTSLIB_VERSION=1.21
ARG JOBLIB_VERSION=0.14.1
ARG MAFFT_VERSION=7.505-1
ARG PSUTIL_VERSION=6.1.1
ARG PYTHON_VERSION=3.13.12
ARG TRUVARI_VERSION=5.4.0
ARG UV_VERSION=0.10.7
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

# Stage 2: .NET runtime
FROM mcr.microsoft.com/dotnet/runtime:${DOTNET_VERSION} AS dotnet_runtime

# Stage 3: uv binary
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv_binary

# Stage 4: Final runtime
FROM mgibio/hap.py:v${HAPPY_VERSION}
ARG BEDOPS_VERSION
ARG BEDTOOLS_VERSION
ARG D2_VERSION
ARG HTSLIB_VERSION
ARG JOBLIB_VERSION
ARG MAFFT_VERSION
ARG PSUTIL_VERSION
ARG PYTHON_VERSION
ARG TRUVARI_VERSION
WORKDIR /app

# Upgrade python2.7 libraries, uninstall vulnerable packages, update system libraries, and build tools
RUN pip install --upgrade --no-cache-dir "joblib==${JOBLIB_VERSION}" "psutil==${PSUTIL_VERSION}" && \
    pip uninstall --y bx-python cryptography cvxopt idna lxml numexpr pillow pip py pyxdg pycrypto setuptools && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gawk \
    apt-transport-https \
    build-essential \
    gcc-10 \
    g++-10 \
    curl \
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
    unzip \
    wget \
    zlib1g-dev && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 100 --slave /usr/bin/g++ g++ /usr/bin/g++-10 && \
    # Install mafft (dependency for truvari)
    wget --quiet "https://mafft.cbrc.jp/alignment/software/mafft_${MAFFT_VERSION}_amd64.deb" && \
    dpkg -i "mafft_${MAFFT_VERSION}_amd64.deb" && \
    rm "mafft_${MAFFT_VERSION}_amd64.deb" && \
    # Build htslib (dependency for bcftools and samtools)
    wget --quiet "https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xjf "htslib-${HTSLIB_VERSION}.tar.bz2" && \
    cd "htslib-${HTSLIB_VERSION}" && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    # Build bcftools
    cd .. && \
    wget --quiet "https://github.com/samtools/bcftools/releases/download/${HTSLIB_VERSION}/bcftools-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xjf "bcftools-${HTSLIB_VERSION}.tar.bz2" && \
    cd "bcftools-${HTSLIB_VERSION}" && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    cd .. && \
    # Build samtools
    wget --quiet "https://github.com/samtools/samtools/releases/download/${HTSLIB_VERSION}/samtools-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xjf "samtools-${HTSLIB_VERSION}.tar.bz2" && \
    cd "samtools-${HTSLIB_VERSION}" && \
    ./configure --prefix=/opt/hap.py && \
    make && make install && \
    cd .. && rm -rf htslib-* samtools-* bcftools-* && \
    # Install precompiled bedtools
    wget --quiet "https://github.com/arq5x/bedtools2/releases/download/v${BEDTOOLS_VERSION}/bedtools.static" && \
    chmod a+x bedtools.static && \
    mv bedtools.static /opt/hap.py/bin/bedtools && \
    # Install bedops
    wget --quiet "https://github.com/bedops/bedops/releases/download/v${BEDOPS_VERSION}/bedops_linux_x86_64-v${BEDOPS_VERSION}.tar.bz2" && \
    mkdir "bedops_linux_x86_64-v${BEDOPS_VERSION}" && \
    tar -jxf "bedops_linux_x86_64-v${BEDOPS_VERSION}.tar.bz2" -C "bedops_linux_x86_64-v${BEDOPS_VERSION}" && \
    cp bedops_linux_x86_64-v"${BEDOPS_VERSION}"/bin/* /opt/hap.py/bin/ && \
    rm -rf bedops_linux_x86_64-v"${BEDOPS_VERSION}"* && \
    # Install d2
    wget --quiet "https://github.com/terrastruct/d2/releases/download/v${D2_VERSION}/d2-v${D2_VERSION}-linux-amd64.tar.gz" && \
    tar -xzf "d2-v${D2_VERSION}-linux-amd64.tar.gz" && \
    mv "d2-v${D2_VERSION}/bin/d2" /opt/hap.py/bin/d2 && \
    rm -rf "d2-v${D2_VERSION}"* && \
    # Build Python
    wget --quiet "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" && \
    tar -xzf "Python-${PYTHON_VERSION}.tgz" && \
    cd "Python-${PYTHON_VERSION}" && \
    ./configure --enable-optimizations && \
    make -j "$(nproc)" && \
    make install && cd .. && rm -rf "Python-${PYTHON_VERSION}" "Python-${PYTHON_VERSION}.tgz" && \
    python3 -m pip wheel pysam==0.23.0 --no-binary pysam -w /wheels/ && \
    apt-get remove --purge -y wget apt-transport-https software-properties-common build-essential && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install .NET runtime
COPY --from=dotnet_runtime /usr/share/dotnet /usr/share/dotnet
RUN ln -sf /usr/share/dotnet/dotnet /usr/bin/dotnet
ENV DOTNET_ROOT=/usr/share/dotnet \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1

# Copy witty.er binary
COPY --from=witty_er_builder /opt/witty.er/Wittyer /witty.er

# Set environment variables
ENV PATH="$PATH:/opt/hap.py/bin:/opt/truvari/bin:/witty.er/bin:/opt/hap.py/libexec/rtg-tools-install"
ENV PATH="$PATH:/usr/bin"

# Update shebangs, create wrapper script, set python defaults, and install truvari
RUN find /opt/hap.py/bin -type f -name "*.py" -exec sed -i 's~#!/usr/bin/python~#!/usr/bin/env python2.7~' {} \; && \
    printf '#!/bin/bash\ndotnet /witty.er/bin/Release/net10.0/Wittyer.dll "$@"\n' > /witty.er/bin/witty.er && \
    chmod +x /witty.er/bin/witty.er && \
    dotnet --info && \
    update-alternatives --install /usr/bin/python python /usr/local/bin/python3 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3 1 && \
    python -m pip install --no-cache-dir --upgrade pip setuptools && \
    python -m venv /opt/truvari && \
    /opt/truvari/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/truvari/bin/pip install --no-cache-dir "truvari==${TRUVARI_VERSION}" && \
    python2.7 -m pip install --no-cache-dir bx-python --no-binary bx-python

# CDI-158 fix som.py inconsistency issue
RUN sed -i 's~True,  # pass_only~not args.inc_nonpass, # account for nonpass in truth vcf~' /opt/hap.py/bin/som.py

# Install project dependencies
COPY --from=uv_binary /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
COPY pyproject.toml uv.lock /app/

RUN pip install --no-cache-dir /wheels/pysam*.whl && \
    uv sync --no-install-project && \
    rm -rf /wheels /tmp/* /root/.cache

# Install project source (This is removed in the CI pipeline)
COPY src/ /app/src/
COPY README.md /app/

RUN uv build --wheel --out-dir dist/ && \
    pip install --no-cache-dir --no-deps dist/*.whl && \
    rm -rf dist/ /root/.cache
