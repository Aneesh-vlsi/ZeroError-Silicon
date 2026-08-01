# config.py
import os
import random
from google import genai
from google.genai import types

DEFAULT_BUS_STATUS = "Status: Clean Light-Workspace Active. Dual-Key high-availability failover pipeline active."

# 🔑 LIVE PRODUCTION KEY MATRIX: Multi-token high-availability fallback pool array
API_KEY_POOL = [
    "AQ.Ab8RN6Km5PQaGxZvoXNQCS5StFcwTHIxg64ql32mdUq349CyfA", # Primary Token Channel
    "AQ.Ab8RN6K7vOyYrsAlgBZ5v-ERRiXB0jdM8_IcwgeVWEpu55DKRQ", # Fallback Token 2
    "AQ.Ab8RN6ILvxwPVR5xCZ-_qmA3ypGoZjPFKJuzergzdSOKwiwc6g", # Fallback Token 3
    "AQ.Ab8RN6KSaizcsYmagIkyHx6LYsxSIaujqT4aTw503eWq_Qu39w"  # Fallback Token 4
]

def safe_api_call(contents, system_instruction, manual_override_key=""):
    TARGET_MODEL = 'gemini-3.5-flash'
    
    # 1. Clean and check the emergency manual token override input box parameter first
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

    # 2. FIXED STRATEGY: Duplicate and shuffle a working array pool list of keys
    # This prevents the client thread from continuously stalling on a single exhausted primary key
    shuffled_pool = list(API_KEY_POOL)
    random.shuffle(shuffled_pool)
    
    for active_key in shuffled_pool:
        # Trace the key back to discover its true index position within your master production pool array
        original_idx = API_KEY_POOL.index(active_key)
        key_label = "Primary Key" if original_idx == 0 else f"Fallback Key {original_idx}"
        
        try:
            # Force a fresh standalone authorization instantiation context
            client = genai.Client(api_key=str(active_key).strip())
            response_text = client.models.generate_content(
                model=TARGET_MODEL, 
                contents=contents, 
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            ).text
            
            if response_text and "QUOTA_ERROR" not in response_text:
                return response_text, key_label
        except Exception:
            # Silently catch token rate blocks and immediately try the next backup token string down the array row
            continue
            
    return "QUOTA_ERROR: All project credentials channels are exhausted.", "All Keys Exhausted"

# ========================================================
# UNTOUCHED: HARDWARE PLATFORM COMPILATION PIPELINE
# ========================================================
def infer_hardware_and_generate_code(board: str, components: str, runtime_key: str) -> tuple[str, str, str]:
    clean_board = board.strip().lower()
    
    # 1. Block high-level software keywords
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

    # 2. Hard validation check for valid microcontroller architectures
    valid_hardware_keywords = ["stm32", "esp32", "esp8266", "arduino", "raspberry", "pico", "atmega", "pic16", "pic18", "msp430", "avr", "teensy", "nordic", "nrf52", "ch32"]
    is_valid_hardware = any(hw_chip in clean_board for hw_chip in valid_hardware_keywords)
    
    if not is_valid_hardware:
        error_msg = (
            f"// ❌ COMPILATION REJECTED: INVALID CHIPSET PROFILE\n"
            f"// Error: '{board}' is not a recognized microcontroller architecture platform.\n"
            f"// The workspace cannot build physical pin connection configurations for non-hardware nodes.\n"
            f"// Expected examples: STM32 H743, ESP32 DevKit, Arduino Uno, Raspberry Pi Pico."
        )
        error_diagram = (
            "### ❌ Unrecognized Hardware Target Platform\n\n"
            f"**Reason:** The entry **'{board}'** is not present in our verified embedded board registry. "
            "Please provide a specific hardware board target so the pin trace engine can map out the connection matrix."
        )
        return error_msg, error_diagram, "No Key Used"

    # 3. If hardware passes verification, run the compilation pipeline
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
        "Acknowledge the user's excellent design goals, use comforting transitions, and guide them calmly through "
        "the board logic in under 3 or 4 clear, rhythmic sentences."
    )
    summary_prompt = f"Kindly explain how this configuration works together like a reassuring friend: Board={board}, Peripherals={components}"
    return safe_api_call(summary_prompt, system_instruction, runtime_key)
# ========================================================
# PYTHON/HTML MULTI-PERIPHERAL PIPELINE (INDUSTRY ENGINE)
# ========================================================
def generate_pure_software_code(language: str, prompt: str, runtime_key: str) -> tuple[str, str]:
    code_prompt = f"Target Environment Language: Pure Front-End HTML5/CSS3\nFunctional Asset Requirements: {prompt}\nWrite comprehensive operational client-side script code directly without any server commentaries or python wrappers."
    
    # SYSTEM PROMPT UPGRADE: Enforces strict fallback coordinate pairs for weather/GPS tracking application structures
    system_instruction = (
        "You are a master front-end software architect and UI/UX expert. Output clean, fully realized HTML5, CSS3, and native JavaScript code text blocks only. "
        "ENTERPRISE-GRADE INDUSTRY UI/UX STANDARDS (MANDATORY):\n"
        "1. MODERN DESIGN SYSTEM: All generated UIs must look like premium, corporate, production-ready enterprise applications or professional dashboards (inspired by modern systems like Apple UI, Tailwind UI, Shadcn, or Material Design). Never generate plain, raw HTML or amateur, basic colorful boxes.\n"
        "2. INDUSTRY COLOR PALETTES: Use cohesive, modern color systems. Prioritize sleek dark tech themes (charcoal deep slate #0f172a, dark navy #1e293b, neon accent borders like cyber cyan or electric mint) or clean clean light enterprise systems (soft greys, subtle whites, balanced primary brand blues). Use semantic color weights for alert tracking badges, links, and operational toggles.\n"
        "3. COHESIVE LAYOUT & GRID SYSTEMS: Structure all panels using professional fluid CSS Flexbox or CSS Grid layouts. Implement uniform border-radius properties (8px to 16px), standardized element gap distributions (16px to 24px), clear visual card structures with soft background elevation shadows, and beautiful layout alignments.\n"
        "4. PREMIUM TYPOGRAPHY SCALE: Enforce a strict typographic hierarchy. Use standard, highly readable system font stacks (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif). Titles must be bold with slight letter spacing, subtitles must use muted secondary text colors (#64748b), and form labels must be compact, uniform, and cleanly aligned.\n"
        "5. COMPONENT CONSISTENCY: Ensure status boxes, interactive slider tracks, control panels, serial output log screens, and metric readouts use perfectly consistent structural styles across the entire display workspace layout.\n"
        "FIX PANEL CLIPPING & OVERLAPPING CONTAINERS: To stop interface boxes from hiding UI components or cutting layout panels short, you MUST NOT use any fixed height values on your elements. Use 'height: auto !important;', 'min-height: max-content;', and explicitly declare 'box-sizing: border-box !important;' on every layout block. Utilize flexible grid streams and columns that dynamically expand downwards so that no card element or navigation link ever clips, overflows, or drops off-screen inside a browser viewport window frame wrapper.\n"
        "AUTOMATIC JAVASCRIPT TEXT CONTRAST SYNCHRONIZER: To completely eliminate text hiding inside dark panels, include an active window initialization JavaScript function that explicitly scans the computed style background color of your main layout views. Write a loop targeting all text nodes (h1, h2, h3, h4, h5, p, span, label, small, a) that sets 'element.style.color = \"#ffffff\"' and 'element.style.opacity = \"1\"' if the parent panel background is dark, and sets 'element.style.color = \"#0f172a\"' if the parent background surface is light. Ensure this runs immediately on 'DOMContentLoaded' to keep text clearly readable at all times.\n"
        "CORE ARCHITECTURE BOUNDARY RESTRICTIONS:\n"
        "1. NO PYTHON/BACKEND: You MUST NOT include any Python code or local server routing. Code must execute entirely within the client-side browser space.\n"
        "2. NETWORK ISOLATION: You MUST NOT invoke external network scripts or remote CDNs. All CSS layouts and JavaScript interaction modules must be completely self-contained and inline.\n"
        "3. NO STORAGE OVERLOADS: Avoid embedding massive, heavy base64 assets that could lag out the local browser execution memory thread.\n"
        "CRITICAL VIEWPORT REQUIREMENT: You MUST include '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">' inside the <head> block. Elements must wrap vertically into a clean single column format using media queries on screens smaller than 768px.\n"
        "MOBILE TOUCH COMPATIBILITY: Intelligently map Mouse Events AND Touch Events together (e.g., link 'touchstart' with 'mousedown') passing '{ passive: false }' and executing 'event.preventDefault()' to disable native browser scroll disruptions while clicking and interacting on screen.\n"
        "DYNAMIC HARDWARE PERIPHERAL ACCESS LAYER: Safely implement standard Web API promise authorization handles only if explicitly requested:\n"
        "1. CAMERA/VIEWFINDER: Embed hidden video tags drawing to requestAnimationFrame canvas tracking layouts natively.\n"
        "2. AUDIO METRICS: Microphone capturing connected directly to localized AudioContext frequency analyzer elements.\n"
        "3. GPS ACCURACY / WEATHER REPORTS / MAPS: If generating weather tracking, environmental sensors, or map dashboards, you MUST implement a dual-pass positioning function. Use 'navigator.geolocation.getCurrentPosition' to pull active coordinates. Crucially, your code MUST include a fallback catch parameter that immediately loads a default city setup (e.g., Latitude: 13.0827, Longitude: 80.2707 for Chennai, or an alternative key major city) if location access times out, is blocked by a sandbox, or is rejected by the user, ensuring the app layout dashboard populates data immediately instead of hanging on initialization scripts.\n"
        "4. ORIENTATION: Window DeviceOrientationEvent orientation tracking loops to calculate device tilting metrics.\n"
        "5. SYSTEM METRICS: Native navigator.getBattery() paths or navigator.vibrate() tactile feedback routines."
    )
    
    raw_software, active_key_used = safe_api_call(code_prompt, system_instruction, runtime_key)
    
    # Cleans formatting wrappers safely using backtick parsing parameters
       #  PASTE THIS CORRECTED REPLACEMENT LINE INSTEAD:
    clean_software = raw_software.replace("```html", "").replace("```css", "").replace("```javascript", "").replace("```", "").strip()

    return clean_software, active_key_used
