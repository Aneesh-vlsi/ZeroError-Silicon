# board_registry.py
#
# Maps a human-typed board name (e.g. "STM32H743", "esp32", "arduino uno")
# to the exact `arduino-cli` FQBN (Fully Qualified Board Name) and the core
# package that must be installed to compile for it. Every core listed here
# is free and open-source, installed once at Docker build time (see the
# Dockerfile snippet), so there is no per-request cost or paid dependency.
#
# HOW TO EXTEND: to support a new board, add one entry. If the board has an
# official or community Arduino core, this is usually all that's needed —
# arduino-cli's own board package already contains the correct CMSIS/HAL/
# clock/linker files for that exact chip, so nothing else has to be built
# by hand.

BOARD_REGISTRY = {
    # ---- Arduino AVR family (core bundled with arduino-cli) ----
    "arduino uno":        {"fqbn": "arduino:avr:uno",       "core": "arduino:avr"},
    "arduino nano":       {"fqbn": "arduino:avr:nano",      "core": "arduino:avr"},
    "arduino mega":       {"fqbn": "arduino:avr:mega",      "core": "arduino:avr"},
    "arduino leonardo":   {"fqbn": "arduino:avr:leonardo",  "core": "arduino:avr"},

    # ---- Espressif ESP32 / ESP8266 family (Espressif's official core) ----
    "esp32":              {"fqbn": "esp32:esp32:esp32",         "core": "esp32:esp32"},
    "esp32s2":             {"fqbn": "esp32:esp32:esp32s2",      "core": "esp32:esp32"},
    "esp32s3":             {"fqbn": "esp32:esp32:esp32s3",      "core": "esp32:esp32"},
    "esp32c3":             {"fqbn": "esp32:esp32:esp32c3",      "core": "esp32:esp32"},
    "esp8266":             {"fqbn": "esp8266:esp8266:generic",  "core": "esp8266:esp8266"},

    # ---- STM32 family (STM32duino community core — free, open-source) ----
    # Selecting the right FQBN variant automatically pulls the matching
    # CMSIS device headers, HAL drivers, startup file, linker script and
    # clock tree config for THAT exact chip from the STM32duino core.
    "stm32f103":  {"fqbn": "STMicroelectronics:stm32:GenF1:pnum=BLUEPILL_F103C8",        "core": "STMicroelectronics:stm32"},
    "stm32f401":  {"fqbn": "STMicroelectronics:stm32:Nucleo_64:pnum=NUCLEO_F401RE",      "core": "STMicroelectronics:stm32"},
    "stm32f411":  {"fqbn": "STMicroelectronics:stm32:Nucleo_64:pnum=NUCLEO_F411RE",      "core": "STMicroelectronics:stm32"},
    "stm32f4":    {"fqbn": "STMicroelectronics:stm32:Nucleo_64:pnum=NUCLEO_F446RE",      "core": "STMicroelectronics:stm32"},
    "stm32g0":    {"fqbn": "STMicroelectronics:stm32:Nucleo_64:pnum=NUCLEO_G071RB",      "core": "STMicroelectronics:stm32"},
    "stm32l0":    {"fqbn": "STMicroelectronics:stm32:Nucleo_64:pnum=NUCLEO_L073RZ",      "core": "STMicroelectronics:stm32"},
    "stm32h743":  {"fqbn": "STMicroelectronics:stm32:Nucleo_144:pnum=NUCLEO_H743ZI",     "core": "STMicroelectronics:stm32"},
    "stm32h7":    {"fqbn": "STMicroelectronics:stm32:Nucleo_144:pnum=NUCLEO_H743ZI",     "core": "STMicroelectronics:stm32"},

    # ---- Raspberry Pi RP2040 (earlephilhower community core) ----
    "raspberry pi pico":  {"fqbn": "rp2040:rp2040:rpipico",  "core": "rp2040:rp2040"},
    "pico":               {"fqbn": "rp2040:rp2040:rpipico",  "core": "rp2040:rp2040"},

    # ---- Nordic nRF52 (Adafruit's community core; also enables BLE OTA later) ----
    "nrf52840":   {"fqbn": "adafruit:nrf52:feather52840",   "core": "adafruit:nrf52"},
}

# How each family is actually flashed once compiled — used by the frontend
# to decide whether to show a one-click "Flash" button (WebSerial-capable)
# or a "Download binary + manual instructions" fallback.
FLASH_METHOD = {
    "arduino:avr":          "webserial-stk500",
    "esp32:esp32":          "webserial-esptool",
    "esp8266:esp8266":      "webserial-esptool",
    "rp2040:rp2040":        "webserial-uf2",       # RP2040 mounts as USB drive in BOOTSEL mode
    "STMicroelectronics:stm32": "webusb-dfu",       # requires BOOT0 into DFU mode
    "adafruit:nrf52":       "webserial-uf2",
}
FLASH_OFFSET = {
    "esp32:esp32":     "0x10000",
    "esp8266:esp8266": "0x0",
}


def resolve_board(user_text: str):
    """Fuzzy-match free-text board input (e.g. 'STM32 H743ZI2 Nucleo') against
    the registry. Returns the matched entry + flash method, or None if this
    board has no known free/open-source Arduino-compatible core — callers
    should fall back to an honest 'not yet supported' message rather than
    guessing."""
    clean = user_text.strip().lower()

    # Exact key match first
    if clean in BOARD_REGISTRY:
        entry = BOARD_REGISTRY[clean]
        return {**entry, "flash_method": FLASH_METHOD.get(entry["core"], "download-only"), "matched_key": clean}

    # Substring match (longest key first, so "stm32h743" wins over "stm32h7")
    for key in sorted(BOARD_REGISTRY.keys(), key=len, reverse=True):
        if key in clean:
            entry = BOARD_REGISTRY[key]
            return {**entry, "flash_method": FLASH_METHOD.get(entry["core"], "download-only"), "matched_key": key}

    return None
