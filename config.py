# config.py
import os
import random
from google import genai
from google.genai import types

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

def safe_api_call(contents, system_instruction, manual_override_key=""):
    TARGET_MODEL = 'gemini-3.5-flash'
    
    clean_override = str(manual_override_key).strip() if manual_override_key else ""
    if clean_override and len(clean_override) > 10:
        try:
            client = genai.Client(api_key=clean_override)
            response_text = client.models.generate_content(
                model=TARGET_MODEL, 
                contents=contents, 
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            ).text
            return response_text, "Manual Override Key"
        except Exception as e:
            return f"// manual override validation crash: {str(e)}", "Manual Override Failed Check"

    # Fallback backup pool rotation strategy if no manual key is typed
    shuffled_pool = list(API_KEY_POOL)
    random.shuffle(shuffled_pool)
    
    if not shuffled_pool:
        return "QUOTA_ERROR: No background system API keys are configured in Render environment variables.", "Keys Missing"
    
    for active_key in shuffled_pool:
        key_label = "System Rotated Key"
        try:
            client = genai.Client(api_key=str(active_key).strip())
            response_text = client.models.generate_content(
                model=TARGET_MODEL, 
                contents=contents, 
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            ).text
            
            if response_text and "QUOTA_ERROR" not in response_text:
                return response_text, key_label
        except Exception:
            continue
            
    return "QUOTA_ERROR: All project credentials channels are exhausted.", "All Keys Exhausted"

def infer_hardware_and_generate_code(board: str, components: str, runtime_key: str) -> tuple[str, str, str]:
    clean_board = board.strip().lower()
    
    restricted_software_terms = ["server", "client", "website", "webpage", "database", "api", "cloud", "application", "app", "ui", "ux", "odometer", "html", "css", "javascript", "my computer", "pc", "laptop"]
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
        return error_msg, error_diagram, "No Key Used"

    valid_hardware_keywords = ["stm32", "esp32", "esp8266", "arduino", "raspberry", "pico", "atmega", "pic16", "pic18", "msp430", "avr", "teensy", "nordic", "nrf52", "ch32"]
    is_valid_hardware = any(hw_chip in clean_board for hw_chip in valid_hardware_keywords)
    
    if not is_valid_hardware:
        error_msg = (
            f"// ❌ COMPILATION REJECTED: INVALID CHIPSET PROFILE\n"
            f"// Error: '{board}' is not a recognized microcontroller architecture platform.\n"
            f"// Expected examples: STM32 H743, ESP32 DevKit, Arduino Uno, Raspberry Pi Pico."
        )
        error_diagram = (
            "### ❌ Unrecognized Hardware Target Platform\n\n"
            f"**Reason:** The entry **'{board}'** is not present in our verified embedded board registry."
        )
        return error_msg, error_diagram, "No Key Used"

    code_prompt = f"Target MCU Board: {board}\nRequested Peripherals: {components}\nWrite full operational C/C++ firmware code directly without markdown wrappers."
    code_instruction = "You are an expert embedded firmware validator. Output clean C/C++ source code text only."
    raw_code, active_key_used = safe_api_call(code_prompt, code_instruction, runtime_key)
    
    if "QUOTA_ERROR" in raw_code:
        return raw_code, "### ❌ Quota system limit exceeded.", active_key_used

    clean_code = raw_code.replace("```cpp", "").replace("```c", "").replace("```", "").strip()

    wiring_prompt = f"Map out explicit pin connections between the board: '{board}' and components: '{components}'. Format as a Markdown comparison table with columns: | {board} Pin | Header Pin Label | Target Device | Target Pin | Assigned Wire Color |"
    wiring_instruction = "You are a hardware layout engineer. Output markdown connection matrices with bold color tags."
    raw_wiring, _ = safe_api_call(wiring_prompt, wiring_instruction, runtime_key)
    clean_wiring = raw_wiring.replace("```text", "").replace("```", "").strip()
    
    return clean_code, clean_wiring, active_key_used

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

def generate_pure_software_code(language: str, prompt: str, runtime_key: str) -> tuple[str, str]:
    code_prompt = f"Target Environment Language: Pure Front-End HTML5/CSS3\nFunctional Asset Requirements: {prompt}\nWrite comprehensive operational client-side script code directly without any server commentaries or python wrappers."
    
    system_instruction = (
        "You are a master front-end software architect and UI/UX expert. Output clean, fully realized HTML5, CSS3, and native JavaScript code text blocks only."
    )
    raw_software, active_key_used = safe_api_call(code_prompt, system_instruction, runtime_key)
    clean_software = raw_software.replace("```html", "").replace("```css", "").replace("```javascript", "").replace("```", "").strip()

    return clean_software, active_key_used
