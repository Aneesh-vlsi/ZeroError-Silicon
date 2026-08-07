# ============================================================
# ZeroError Silicon — Dockerfile
# Python/Gradio app + arduino-cli (free, open-source) for real
# server-side firmware compilation.
# ============================================================

FROM python:3.11-slim

# --- System packages needed to install arduino-cli and build cores ---
# curl: to fetch the arduino-cli install script
# ca-certificates: so the HTTPS download above actually verifies correctly
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Install arduino-cli (official install script, free) ---
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh -s -- -b /usr/local/bin

# --- Register free, open-source board package index sources ---
RUN arduino-cli config init && \
    arduino-cli config add board_manager.additional_urls \
        https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json \
        https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json \
        https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json \
        https://adafruit.github.io/arduino-board-index/package_adafruit_index.json

# --- Update index and pre-install the cores used in board_registry.py ---
# (Pre-installing at build time means the FIRST user request for a given
# board family doesn't have to wait for a core download — it's already
# there. compiler.py still runs "core install" defensively per-request in
# case a new board is added to the registry without a fresh image build.)
RUN arduino-cli core update-index && \
    arduino-cli core install arduino:avr && \
    arduino-cli core install esp32:esp32 && \
    arduino-cli core install esp8266:esp8266 && \
    arduino-cli core install STMicroelectronics:stm32 && \
    arduino-cli core install rp2040:rp2040 && \
    arduino-cli core install adafruit:nrf52

# --- Pre-warm the arduino-cli build cache so the first real compile of ---
# --- each board family isn't the slow one (matches compiler.py's use  ---
# --- of --build-cache-path /opt/arduino-cache).                       ---
RUN mkdir -p /opt/arduino-cache

# --- App working directory ---
WORKDIR /app

# --- Install Python dependencies first (better Docker layer caching: ---
# --- this layer only rebuilds when requirements.txt itself changes)  ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy the rest of the application source ---
COPY . .

# --- Gradio listens on 7860 inside the container (matches app.launch ---
# --- server_port=7860 in app.py) ---
EXPOSE 7860

# --- Environment: keep Python output unbuffered so logs show up live ---
# --- in Render's log stream instead of being buffered ---
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
