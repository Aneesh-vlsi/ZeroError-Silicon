# Dockerfile
# This replaces Render's automatic Python buildpack with a container that
# also has arduino-cli + board cores installed — needed for the real
# compile/flash pipeline.

FROM python:3.11-slim

# --- System dependencies ---
# curl: needed to download arduino-cli
# ca-certificates: needed for curl to verify HTTPS (missing on slim images)
# tar: needed to unpack the arduino-cli download
# build-essential: some board cores need a C toolchain during install
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    tar \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Install arduino-cli (free, official install script) ---
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh -s -- -b /usr/local/bin

# --- Register free, open-source board package index sources ---
RUN arduino-cli config init && \
    arduino-cli config add board_manager.additional_urls \
        https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json \
        https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json \
        https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json \
        https://adafruit.github.io/arduino-board-index/package_adafruit_index.json

# --- Pre-install board cores at build time (so the first user request is fast) ---
RUN arduino-cli core update-index && \
    arduino-cli core install arduino:avr && \
    arduino-cli core install esp32:esp32 && \
    arduino-cli core install esp8266:esp8266 && \
    arduino-cli core install STMicroelectronics:stm32 && \
    arduino-cli core install rp2040:rp2040 && \
    arduino-cli core install adafruit:nrf52

# --- Set up the Python app ---
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
