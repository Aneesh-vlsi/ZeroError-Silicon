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

# --- Install arduino-cli (free, direct pinned-version download) ---
# Using the install.sh script queries GitHub's API to find the "latest"
# version, which can get rate-limited on shared cloud build IPs. Downloading
# a specific release tarball directly avoids that API call entirely.
RUN curl -fsSL -o /tmp/arduino-cli.tar.gz \
    https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Linux_64bit.tar.gz \
    && tar -xzf /tmp/arduino-cli.tar.gz -C /usr/local/bin arduino-cli \
    && rm /tmp/arduino-cli.tar.gz \
    && arduino-cli version

# --- Register free, open-source board package index sources ---
RUN arduino-cli config init && \
    arduino-cli config add board_manager.additional_urls \
        https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json \
        https://arduino.esp8266.com/stable/package_esp8266com_index.json \
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

# --- Pre-warm the build cache for the most common boards ---
# The FIRST compile for any given board is always slow because it has to
# compile the whole core library, not just the sketch. Doing that once here,
# at build time, means real users hitting the most common boards get a fast
# compile immediately — the slow part already happened during deployment.
RUN mkdir -p /tmp/warm-sketch && \
    echo "void setup() {} void loop() {}" > /tmp/warm-sketch/warm-sketch.ino && \
    arduino-cli compile --fqbn arduino:avr:uno /tmp/warm-sketch --build-cache-path /opt/arduino-cache || true && \
    arduino-cli compile --fqbn esp32:esp32:esp32 /tmp/warm-sketch --build-cache-path /opt/arduino-cache || true && \
    arduino-cli compile --fqbn esp8266:esp8266:generic /tmp/warm-sketch --build-cache-path /opt/arduino-cache || true && \
    rm -rf /tmp/warm-sketch

# --- Set up the Python app ---
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
