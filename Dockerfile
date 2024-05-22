FROM ubuntu:22.04

# Install additional dependencies
RUN apt update && apt upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    apt-transport-https \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    docker.io \
    fdkaac \
    git \
    gnupg \
    gnuradio \
    gnuradio-dev \
    gr-funcube \
    gr-iqbal \
    libairspy-dev \
    libairspyhf-dev \
    libbladerf-dev \
    libboost-all-dev \
    libcurl4-openssl-dev \
    libfreesrp-dev \
    libgmp-dev \
    libhackrf-dev \
    libmirisdr-dev \
    liborc-0.4-dev \
    libpthread-stubs0-dev \
    libsndfile1-dev \
    libsoapysdr-dev \
    libssl-dev \
    libuhd-dev \
    libusb-dev \
    libusb-1.0-0-dev \
    libxtrx-dev \
    pkg-config \
    software-properties-common \
    sox \
    python3.11 \
    python3.11-distutils \
    python3.11-venv \
    python3-pip \
    python3-setuptools \
    python3-dev \
    libpaho-mqtt-dev \
    libpaho-mqttpp-dev \
    ffmpeg \
    && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Fix the error message level for SmartNet

RUN sed -i 's/log_level = debug/log_level = info/g' /etc/gnuradio/conf.d/gnuradio-runtime.conf

# Compile librtlsdr-dev 2.0 for SDR-Blog v4 support and other updates
# Ubuntu 22.04 LTS has librtlsdr 0.6.0
RUN cd /tmp && \
  git clone https://github.com/steve-m/librtlsdr.git && \
  cd librtlsdr && \
  mkdir build && \
  cd build && \
  cmake .. && \
  make -j$(nproc) && \
  make install && \
  ldconfig && \
  cd /tmp && \
  rm -rf librtlsdr

# Compile gr-osmosdr ourselves using a fork with various patches included
RUN cd /tmp && \
  git clone https://github.com/racerxdl/gr-osmosdr.git && \
  cd gr-osmosdr && \
  mkdir build && \
  cd build && \
  cmake -DENABLE_NONFREE=TRUE .. && \
  make -j$(nproc) && \
  make install && \
  ldconfig && \
  cd /tmp && \
  rm -rf gr-osmosdr

RUN cd / &&  \
    mkdir src &&  \
    cd src && \
    git clone -b rc/v5.0 https://github.com/robotastic/trunk-recorder.git && \
    git clone -b test/autobuild https://github.com/taclane/trunk-recorder-mqtt-status.git /src/trunk-recorder/user-plugins && \
    cd trunk-recorder && \
    mkdir build && \
    cd build && \
    cmake ../ && \
    make -j$(nproc) && \
    make install


# Clone and build Trunk Recorder MQTT Status Plugin
#RUN git clone https://github.com/taclane/trunk-recorder-mqtt-status.git \
#    && cd trunk-recorder-mqtt-status \
#    && mkdir build && cd build \
#    && cmake ../ \
#    && make install \
#    && cd ../.. && rm -rf trunk-recorder-mqtt-status

# Upgrade PIP
RUN pip3 install --upgrade pip

# Set the working directory in the container
WORKDIR /app

# Install iCAD TR Uploader
RUN git clone https://github.com/TheGreatCodeholio/icad_tr_uploader.git && \
    rm -rf icad_tr_uploader/etc && \
    cd icad_tr_uploader &&  \
    pip3 install -r requirements.txt

# GNURadio requires a place to store some files, can only be set via $HOME env var.
ENV HOME=/tmp

CMD trunk-recorder --config=/app/config.json