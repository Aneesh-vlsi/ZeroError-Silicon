import os
import random
import re
import base64
import traceback
from google import genai
from google.genai import types
from board_registry import resolve_board
from compiler import compile_sketch

DEFAULT_BUS_STATUS = "Status: Clean Light-Workspace Active. Dual-Key high-availability failover pipeline active."

# 🔑 SECURE PRODUCTION KEY MATRIX: Dynamically reads from Render's Environment Secrets Panel
API_KEY_POOL = [
    os.environ.get("GEMINI_KEY_1", ""),
    os.environ.get("GEMINI_KEY_2", ""),
    os.environ.get("GEMINI_KEY_3", ""),
    os.environ.get("GEMINI_KEY_4", ""),
    os.environ.get("GEMINI_KEY_5", ""),
    os.environ.get("GEMINI_KEY_6", ""),
    os.environ.get("GEMINI_KEY_7", ""),
    os.environ.get("GEMINI_KEY_8", ""),
    os.environ.get("GEMINI_KEY_9", ""),
    os.environ.get("GEMINI_KEY_10", "")
]

# Filter out empty or unconfigured variable placeholders
API_KEY_POOL = [key for key in API_KEY_POOL if key.strip()]

# ------------------------------------------------------------------
# Google retires Gemini model IDs on a rolling basis — as of this writing:
#   - gemini-1.5-flash : SHUT DOWN (fully removed, always 404s)
#   - gemini-2.0-flash : SHUT DOWN June 1, 2026
#   - gemini-2.5-flash : still live, but scheduled to shut down Oct 16, 2026
#   - gemini-3.5-flash / gemini-3.6-flash : current generation, live, no
#     shutdown date announced
#
# Rather than hardcode one ID that will inevitably go stale again, we try
# a short list of currently-live models in order (newest-first), and only
# move to the next API key once every model ID has been tried against it.
# When Google deprecates one of these, just drop/replace the entry here —
# check https://ai.google.dev/gemini-api/docs/deprecations for the current
# list rather than assuming.
# ------------------------------------------------------------------
CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]


def _try_generate(client, contents, system_instruction):
    """Try each candidate model in order against a single client. Returns
    (text, model_used) on success, raises the last exception on total failure."""
    last_exc = None
    for model_name in CANDIDATE_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            return response.text, model_name
        except Exception as e:
            last_exc = e
            continue
    raise last_exc if last_exc else RuntimeError("No candidate models were attempted.")


def safe_api_call(contents, system_instruction, manual_override_key=""):
    clean_override = str(manual_override_key).strip() if manual_override_key else ""
    if clean_override and len(clean_override) > 10:
        try:
            client = genai.Client(api_key=clean_override)
            response_text, model_used = _try_generate(client, contents, system_instruction)
            return response_text, f"Manual Override Key ({model_used})"
        except Exception as e:
            print("=== safe_api_call: manual override key failed ===")
            traceback.print_exc()
            return f"// manual override validation crash: {str(e)}", "Manual Override Failed Check"

    # Fallback backup pool rotation strategy if no manual key is typed
    shuffled_pool = list(API_KEY_POOL)
    random.shuffle(shuffled_pool)

    if not shuffled_pool:
        return "QUOTA_ERROR: No background system API keys are configured in Render environment variables.", "Keys Missing"

    last_error = None
    for active_key in shuffled_pool:
        try:
            client = genai.Client(api_key=str(active_key).strip())
            response_text, model_used = _try_generate(client, contents, system_instruction)

            if response_text and "QUOTA_ERROR" not in response_text:
                return response_text, f"System Rotated Key ({model_used})"
        except Exception as e:
            last_error = e
            # Log the real cause to stdout/stderr so it shows up in Render
            # logs — silently swallowing this is what made past failures
            # look like a generic "Error" bubble with no clue why.
            print(f"=== safe_api_call: key failed ({type(e).__name__}): {e} ===")
            continue

    detail = f" Last error: {type(last_error).__name__}: {last_error}" if last_error else ""
    return f"QUOTA_ERROR: All project credentials channels are exhausted.{detail}", "All Keys Exhausted"


def infer_hardware_and_generate_code(board: str, components: str, runtime_key: str) -> tuple[str, str, str, dict]:
    """Generates AND actually compiles firmware for the requested board.

    Returns (code_text, wiring_diagram, key_used, compile_info) where
    compile_info is a dict the app layer uses to drive the Flash button:
        {
          "compiled": bool,
          "binary_b64": str,       # base64 binary, empty if not compiled
          "binary_ext": str,       # "bin" / "hex" / "uf2"
          "flash_method": str,     # "webserial-esptool" / "webserial-stk500" /
                                    # "webserial-uf2" / "webusb-dfu" / "download-only"
          "fqbn": str,
        }
    """
    clean_board = board.strip().lower()

    restricted_software_terms = ["server", "client", "website", "webpage", "database", "api", "cloud", "application", "app", "ui", "ux", "odometer", "html", "css", "javascript", "my computer", "pc", "laptop"]
    empty_compile_info = {"compiled": False, "binary_b64": "", "binary_ext": "", "flash_method": "download-only", "fqbn": ""}

    if any(term == clean_board for term in restricted_software_terms) or len(clean_board) < 3:
        error_msg = (
            f"// ❌ COMPILATION TERMINATED: TARGET BOUNDARY CRASH\n"
            f"// Error: '{board}' is categorized as high-level software, not an embedded chip.\n"
            f"// Please move to the next tab for general software scripts."
        )
        error_diagram = (
            "### ❌ Hardware Compilation Boundary Triggered\n\n"
            f"**Reason:** The token **'{board}'** does not represent a physical micro-controller evaluation board."
        )
        return error_msg, error_diagram, "No Key Used", empty_compile_info

    board_match = resolve_board(board)

    if not board_match:
        # Honest fallback: this board has no free/open-source Arduino-compatible
        # core registered yet, so we can't actually compile+flash it. We say so
        # clearly instead of silently generating code that may not build.
        error_msg = (
            f"// ⚠️ '{board}' IS NOT YET IN THE FREE COMPILE/FLASH REGISTRY\n"
            f"// This board has no free, open-source Arduino-compatible core registered in\n"
            f"// this app yet, so real compilation + one-click flashing can't be offered for it.\n"
            f"// Recognized families right now: Arduino AVR, ESP32/ESP8266, STM32 (Nucleo/BluePill),\n"
            f"// Raspberry Pi Pico (RP2040), Nordic nRF52.\n"
            f"// You can still request AI-generated reference code below, but it will need to be\n"
            f"// compiled manually with that chip's own vendor toolchain."
        )
        # Still offer best-effort reference code generation, clearly labeled as unverified.
        code_prompt = f"Target MCU Board: {board}\nRequested Peripherals: {components}\nWrite full operational C/C++ firmware code directly without markdown wrappers. This is reference code only — it has not been compiled or verified."
        code_instruction = "You are an expert embedded firmware assistant. Output clean C/C++ source code text only. Clearly this is unverified reference code for a board with no available toolchain."
        raw_code, active_key_used = safe_api_call(code_prompt, code_instruction, runtime_key)
        clean_code = raw_code.replace("```cpp", "").replace("```c", "").replace("```", "").strip()
        full_msg = error_msg + "\n\n// ---- UNVERIFIED REFERENCE CODE BELOW ----\n\n" + clean_code

        wiring_prompt = f"Map out explicit pin connections between the board: '{board}' and components: '{components}'. Format as a Markdown comparison table with columns: | {board} Pin | Header Pin Label | Target Device | Target Pin | Assigned Wire Color |"
        wiring_instruction = "You are a hardware layout engineer. Output markdown connection matrices with bold color tags."
        raw_wiring, _ = safe_api_call(wiring_prompt, wiring_instruction, runtime_key)
        clean_wiring = raw_wiring.replace("```text", "").replace("```", "").strip()

        return full_msg, clean_wiring, active_key_used, empty_compile_info

    # --- Board recognized: generate an Arduino-style sketch (setup/loop) ---
    # This is far more reliable for an LLM to get right than raw register-level
    # HAL code, and it's exactly the format arduino-cli expects — so the AI's
    # job is just "write correct application logic", while arduino-cli supplies
    # the real CMSIS/HAL/clock/linker files for the exact chip automatically.
    sketch_prompt = (
        f"Target board: {board} (FQBN: {board_match['fqbn']})\n"
        f"Requested peripherals/behavior: {components}\n"
        "Write a complete Arduino-style sketch (setup() and loop() functions) implementing this. "
        "Use only standard Arduino core functions and widely-available libraries. "
        "Output raw code only, no markdown fences, no commentary."
    )
    sketch_instruction = (
        "You are an expert embedded firmware engineer writing Arduino-core-compatible sketches. "
        "Output ONLY valid .ino sketch code (setup/loop style). Never use raw register/HAL calls unless "
        "no Arduino-core equivalent exists. This code will be compiled for real with arduino-cli, so it "
        "must be syntactically correct and complete."
    )
    raw_sketch, active_key_used = safe_api_call(sketch_prompt, sketch_instruction, runtime_key)

    if "QUOTA_ERROR" in raw_sketch:
        return raw_sketch, "### ❌ Quota system limit exceeded.", active_key_used, empty_compile_info

    clean_sketch = raw_sketch.replace("```cpp", "").replace("```ino", "").replace("```", "").strip()

    # --- REAL COMPILATION, not just AI output ---
    success, binary_path, compile_log = compile_sketch(clean_sketch, board_match["fqbn"], board_match["core"])

    if success:
        with open(binary_path, "rb") as f:
            binary_bytes = f.read()
        binary_b64 = base64.b64encode(binary_bytes).decode("ascii")
        binary_ext = binary_path.rsplit(".", 1)[-1]
        status_note = f"// ✅ COMPILED SUCCESSFULLY for {board_match['fqbn']}\n// This is a REAL compiled binary, verified by arduino-cli — not just AI-generated text.\n\n"
        final_code = status_note + clean_sketch
        compile_info = {
            "compiled": True,
            "binary_b64": binary_b64,
            "binary_ext": binary_ext,
            "flash_method": board_match["flash_method"],
            "fqbn": board_match["fqbn"],
        }
    else:
        status_note = (
            f"// ❌ COMPILATION FAILED for {board_match['fqbn']}\n"
            f"// The AI-generated sketch did not compile. Build log:\n// "
            + compile_log.replace("\n", "\n// ") + "\n\n"
        )
        final_code = status_note + clean_sketch
        compile_info = empty_compile_info

    wiring_prompt = f"Map out explicit pin connections between the board: '{board}' and components: '{components}'. Format as a Markdown comparison table with columns: | {board} Pin | Header Pin Label | Target Device | Target Pin | Assigned Wire Color |"
    wiring_instruction = "You are a hardware layout engineer. Output markdown connection matrices with bold color tags."
    raw_wiring, _ = safe_api_call(wiring_prompt, wiring_instruction, runtime_key)
    clean_wiring = raw_wiring.replace("```text", "").replace("```", "").strip()

    return final_code, clean_wiring, active_key_used, compile_info


def generate_voice_explanation(board: str, components: str, runtime_key: str) -> tuple[str, str]:
    restricted_software_terms = ["server", "client", "website", "webpage", "application", "app", "my computer", "pc"]
    if board.strip().lower() in restricted_software_terms:
        return "Let's pause and check this setup together. It looks like the target selected isn't an embedded board.", "No Key Used"

    system_instruction = (
        "You are an incredibly patient, warm, and highly empathetic hardware engineering mentor. "
        "Speak in an encouraging, slow, steady, reassuring tone like a helpful peer. "
        "Guide them calmly through the board logic in under 3 or 4 clear, rhythmic sentences."
    )
    summary_prompt = f"Kindly explain how this configuration works together like a reassuring friend: Board={board}, Peripherals={components}"
    return safe_api_call(summary_prompt, system_instruction, runtime_key)


# ============================================================
# SECURE-CONTEXT / PERMISSIONS SAFETY NET (software pipeline)
# ============================================================
_SECURE_CONTEXT_GUARD_SNIPPET = """
<script>
(function() {
    function isInsecureContext() {
        var isLocalhost = ["localhost", "127.0.0.1", "[::1]"].indexOf(location.hostname) !== -1;
        return location.protocol !== "https:" && !isLocalhost;
    }
    function showGuardBanner(message) {
        if (document.getElementById("zes-secure-guard-banner")) return;
        var banner = document.createElement("div");
        banner.id = "zes-secure-guard-banner";
        banner.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:999999;background:#fef2f2;border-bottom:2px solid #fca5a5;color:#991b1b;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:13px;font-weight:600;padding:10px 14px;line-height:1.4;text-align:center;";
        banner.innerHTML = message;
        document.body.insertBefore(banner, document.body.firstChild);
    }
    if (isInsecureContext()) {
        window.__ZES_INSECURE_CONTEXT__ = true;
        document.addEventListener("DOMContentLoaded", function() {
            showGuardBanner("⚠️ Camera, microphone, and location features need a secure connection. Open this file via <code>http://localhost</code> or host it online with HTTPS (e.g. Netlify, GitHub Pages) &mdash; it will not work when opened directly as a local file, especially on mobile.");
        });
    }
})();
</script>
"""


def _inject_secure_context_guard(html_code: str) -> str:
    result = html_code
    if "viewport" not in result.lower():
        viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        if re.search(r"<head[^>]*>", result, re.IGNORECASE):
            result = re.sub(r"(<head[^>]*>)", r"\1\n" + viewport_tag, result, count=1, flags=re.IGNORECASE)
        else:
            result = viewport_tag + result
    if re.search(r"<body[^>]*>", result, re.IGNORECASE):
        result = re.sub(r"(<body[^>]*>)", r"\1\n" + _SECURE_CONTEXT_GUARD_SNIPPET, result, count=1, flags=re.IGNORECASE)
    else:
        result = _SECURE_CONTEXT_GUARD_SNIPPET + result
    return result


def generate_pure_software_code(language: str, prompt: str, runtime_key: str) -> tuple[str, str]:
    code_prompt = (
        f"Functional Asset Requirements: {prompt}\n\n"
        "Build this as a single, fully self-contained, REAL, WORKING HTML5 file "
        "(inline CSS and JavaScript only, no build tools, no server, no backend). "
        "It must be genuinely functional, not a mockup or static demo."
    )

    system_instruction = (
        "You are a master front-end software architect. Output ONLY a single complete "
        "HTML5 document (inline <style> and <script>) implementing the user's request as "
        "REAL, WORKING functionality — never a static mockup, placeholder, or fake animation "
        "pretending to be the real feature. Follow these rules precisely:\n\n"
        "1. MOBILE + DESKTOP COMPATIBLE: Always include "
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">, and use "
        "responsive layouts (flexbox/grid, relative units) that work on small phone screens "
        "and desktop windows alike. Buttons and tap targets must be large enough for touch.\n\n"
        "2. CAMERA / OBJECT DETECTION / COMPUTER VISION requests: use "
        "navigator.mediaDevices.getUserMedia({video:true}) to access the real camera into a "
        "<video> element. For AI object/image detection, load TensorFlow.js and the "
        "coco-ssd model from a public CDN (e.g. https://cdn.jsdelivr.net/npm/@tensorflow/tfjs "
        "and @tensorflow-models/coco-ssd), run real inference on the live video frames, and "
        "draw real bounding boxes/labels on a <canvas> overlay. Wrap camera access in "
        "try/catch and show a clear on-screen message if permission is denied or unavailable.\n\n"
        "3. LOCATION / MAPS / 'REAL-TIME TRAFFIC IN MY LOCALITY' requests: use "
        "navigator.geolocation.getCurrentPosition / watchPosition to get the user's real "
        "coordinates, and render a real interactive map using Leaflet.js + OpenStreetMap "
        "tiles loaded from CDN (https://unpkg.com/leaflet), centered on the user's real "
        "location with a marker. Since live traffic-flow data requires a paid provider key "
        "(e.g. TomTom, Google Maps, HERE), include a labeled input field where the user can "
        "paste their own API key to enable a live traffic overlay, and clearly state in the "
        "UI when the app is showing 'Demo/simulated traffic data' versus real data from a "
        "provided key. Never silently fabricate data and present it as real.\n\n"
        "4. PERMISSIONS: Always wrap getUserMedia/geolocation calls in try/catch, and show a "
        "clear, visible on-page message (not just a console log or alert()) explaining what "
        "went wrong and what the user can do (e.g. 'Camera permission denied — please allow "
        "camera access in your browser settings and reload').\n\n"
        "5. SELF-CONTAINED: Only reference external resources via public CDN <script>/<link> "
        "tags (jsdelivr, unpkg, cdnjs). No npm install, no build step, no server-side code, "
        "no relative imports to files that don't exist.\n\n"
        "6. Output raw HTML only — no markdown code fences, no commentary before or after "
        "the document."
    )

    raw_software, active_key_used = safe_api_call(code_prompt, system_instruction, runtime_key)

    if "QUOTA_ERROR" in raw_software:
        return raw_software, active_key_used

    clean_software = raw_software.replace("```html", "").replace("```css", "").replace("```javascript", "").replace("```", "").strip()
    clean_software = _inject_secure_context_guard(clean_software)

    return clean_software, active_key_used
