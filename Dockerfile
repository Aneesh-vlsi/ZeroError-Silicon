# Add this to your existing Dockerfile (or create one if you're currently
# using Render's native Python buildpack — you'll need to switch to a
# Dockerfile-based Render service to run arduino-cli).
#
# Every tool and board core installed below is free and open-source.
# This only needs to happen once per deploy (baked into the image), not
# per-request, so it doesn't slow down or cost anything at runtime.

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
