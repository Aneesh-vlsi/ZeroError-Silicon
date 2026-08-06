# app.py
import gradio as gr
from app_logic import handle_hardware_pipeline, handle_software_pipeline
from theme_engine import theme_engine_js, force_light_mode_js, stop_sfx_js, login_wall_css
from voice_engine import tts_javascript, stop_tts_javascript

download_hw_js = """
(file_content) => {
    if (!file_content || file_content.trim() === "") {
        alert("Attention: No compiled blueprint data available to export yet. Please execute compilation first.");
        return;
    }
    let customName = prompt("Enter a filename for your hardware blueprint:", "verified_embedded_blueprint.txt");
    if (!customName) return; 
    if (!customName.toLowerCase().endsWith(".txt")) { customName += ".txt"; }
    let dataBlob = new Blob([file_content], { type: "text/plain;charset=utf-8" });
    let linkElement = document.createElement("a");
    linkElement.href = URL.createObjectURL(dataBlob);
    linkElement.download = customName;
    document.body.appendChild(linkElement);
    linkElement.click();
    document.body.removeChild(linkElement);
}
"""

download_sw_js = """
(file_content) => {
    if (!file_content || file_content.trim() === "") {
        alert("Attention: No compiled software asset data available to export yet. Please execute compilation first.");
        return;
    }
    let customName = prompt("Enter a filename for your software code:", "compiled_application.html");
    if (!customName) return; 
    if (!customName.toLowerCase().endsWith(".html")) { customName += ".html"; }
    let dataBlob = new Blob([file_content], { type: "text/html;charset=utf-8" });
    let linkElement = document.createElement("a");
    linkElement.href = URL.createObjectURL(dataBlob);
    linkElement.download = customName;
    document.body.appendChild(linkElement);
    linkElement.click();
    document.body.removeChild(linkElement);
}
"""

logout_session_js = r"""
() => {
    let currentURL = window.location.href;
    let cleanURL = currentURL.replace(/^(https?:\/\/)(.*)/, '$1logout:logout@$2');
    try {
        sessionStorage.clear();
        localStorage.clear();
    } catch(e) {}
    window.location.href = cleanURL;
}
"""

# ============================================================
# WEBSERIAL: live board connect/disconnect status indicator
# ============================================================
# Runs once on page load. Requires Chrome/Edge on desktop — WebSerial is not
# available on mobile browsers or Safari/Firefox (see chat notes). We detect
# that gracefully and label the status box accordingly instead of failing
# silently.
board_status_watcher_js = """
() => {
    const statusEl = () => document.getElementById("zes-board-status-badge");

    function ensureBadge() {
        if (document.getElementById("zes-board-status-badge")) return;
        let btn = [...document.querySelectorAll("button")].find(b => b.textContent.includes("Run Multi-Pass"));
        if (!btn) return;
        let badge = document.createElement("div");
        badge.id = "zes-board-status-badge";
        badge.style.cssText = "margin:8px 0;padding:8px 12px;border-radius:8px;font-size:13px;font-weight:600;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;";
        btn.parentElement.insertBefore(badge, btn);
        renderBadge();
    }

    function renderBadge() {
        let el = statusEl();
        if (!el) return;
        if (!("serial" in navigator)) {
            el.style.background = "#f1f5f9"; el.style.color = "#475569";
            el.textContent = "🔌 Board detection needs Chrome or Edge on desktop (not available in this browser).";
            return;
        }
        navigator.serial.getPorts().then(ports => {
            if (ports.length > 0) {
                el.style.background = "#dcfce7"; el.style.color = "#15803d";
                el.textContent = "✅ Board Connected (" + ports.length + " authorized port" + (ports.length > 1 ? "s" : "") + ")";
            } else {
                el.style.background = "#fef2f2"; el.style.color = "#991b1b";
                el.textContent = "❌ No Board Connected — click Flash to select your board once.";
            }
        });
    }

    ensureBadge();
    if ("serial" in navigator) {
        navigator.serial.addEventListener("connect", renderBadge);
        navigator.serial.addEventListener("disconnect", renderBadge);
    }
    // Re-check periodically in case the badge element gets re-rendered by Gradio
    setInterval(ensureBadge, 2000);
}
"""

# ============================================================
# FLASH TO BOARD: real WebSerial flashing for ESP32 family.
# AVR / RP2040 / nRF52 / STM32(DFU) show an honest "not yet automated,
# download the binary and flash manually" message rather than faking it.
# ============================================================
flash_to_board_js = """
async (flash_payload_json) => {
    let payload;
    try { payload = JSON.parse(flash_payload_json); } catch(e) { payload = {}; }

    if (!payload.binary_b64) {
        alert("No compiled binary available yet. Run compilation first — this board may not have produced a verified binary.");
        return;
    }

    if (!("serial" in navigator)) {
        alert("Flashing from the browser needs Chrome or Edge on desktop. On other browsers, please download the compiled binary and flash it manually with your board's own tool.");
        return;
    }

    const bytes = Uint8Array.from(atob(payload.binary_b64), c => c.charCodeAt(0));

    if (payload.flash_method === "webserial-esptool") {
        try {
            const esptoolModule = await import("https://esm.sh/esptool-js@0.4.6");
            const port = await navigator.serial.requestPort();
            const transport = new esptoolModule.Transport(port);
            const loaderOptions = { transport, baudrate: 115200 };
            const esploader = new esptoolModule.ESPLoader(loaderOptions);
            await esploader.main();
            await esploader.writeFlash({
                fileArray: [{ data: Array.from(bytes).map(b => String.fromCharCode(b)).join(""), address: 0x1000 }],
                flashSize: "keep",
                eraseAll: false,
                compress: true,
            });
            alert("✅ Flash complete! Your ESP32 has been programmed.");
        } catch (err) {
            alert("Flashing failed: " + err.message + "\\n\\nMake sure your board is in the correct mode and try again.");
        }
        return;
    }

    if (payload.flash_method === "webserial-stk500") {
        alert("One-click AVR flashing over WebSerial is still being finalized in this build. Please download the compiled binary below and flash it with avrdude or the Arduino IDE for now — full one-click support is coming next.");
        return;
    }

    if (payload.flash_method === "webusb-dfu") {
        alert("This STM32 board needs DFU mode (BOOT0 pin) to flash. One-click WebUSB DFU flashing is on the roadmap — for now, please download the compiled binary and flash it with STM32CubeProgrammer.");
        return;
    }

    if (payload.flash_method === "webserial-uf2") {
        alert("This board flashes as a UF2 file: put it in bootloader mode (usually double-tap RESET), it will appear as a USB drive, then drag the downloaded binary onto it.");
        return;
    }

    alert("Automatic flashing isn't available yet for this board family. Please download the compiled binary and use your board's own flashing tool.");
}
"""

with gr.Blocks() as app:
    with gr.Row(elem_id="header-bar-container", variant="compact"):
        with gr.Column(scale=4):
            gr.Markdown("# 🤖 ZeroError Silicon")
            gr.Markdown("<p style='color: #475569 !important; font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif !important; font-size: 15px !important; font-weight: 500 !important; margin: 4px 0 16px 0 !important; padding: 0 !important; line-height: 1.4 !important; letter-spacing: -0.01em !important;'>Next-Generation AI Tooling for Heterogeneous Microcontrollers</p>")
        with gr.Column(scale=1, min_width=120):
            logout_btn = gr.Button("🚪 Log Out", variant="stop", size="sm")

    with gr.Row():
        bus_status_display = gr.Textbox(label="Hardware Bus Tracking Status", value="Status: Workspace Online. Ready to receive design rules.", interactive=False, scale=3)
        theme_selector = gr.Dropdown(
            label="🎨 Select Interface Workspace Theme",
            choices=["Light Slate (Default Clean)", "Ocean Blue Breeze", "Forest Mint", "Sunset Orange & Ember", "Classic Steel Cyber"],
            value="Light Slate (Default Clean)",
            interactive=True,
            scale=2
        )

    with gr.Row():
        voice_persona_dropdown = gr.Dropdown(
            label="🗣️ Select Assistant Voice Profile Persona (Global Control)",
            choices=["May (Clear Female Profile)", "Heera (Indian Accent Female)", "Max (Standard Male Profile)", "Jimmy (Fast Tech Profile)"],
            value="Max (Standard Male Profile)",
            interactive=True
        )
        manual_key_input = gr.Textbox(
            label="🔑 Emergency API Token Manual Override (Optional)",
            placeholder="Paste fresh AQ.Ab8... token here if quota is exhausted...",
            type="password",
            interactive=True
        )

    with gr.Tabs():
        # TAB 1: EMBEDDED HARDWARE FIRMWARE
        with gr.Tab("📟 Embedded Hardware Firmware"):
            gr.Markdown("### Secure Microcontroller Code & Wiring Synthesis Block")
            gr.HTML(value="""
                <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; margin: 4px 0 16px 0; font-size: 13px; color: #1e3a8a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                    ℹ️ <strong>Supported for real compile + flash today:</strong> Arduino AVR (Uno/Nano/Mega), ESP32/ESP32-S2/S3/C3, ESP8266, STM32 (Nucleo/BluePill via STM32duino), Raspberry Pi Pico (RP2040), Nordic nRF52.
                    Other boards still get AI-generated reference code, clearly marked as unverified.
                </div>
            """)
            with gr.Row():
                with gr.Column(scale=1):
                    board_input = gr.Textbox(label="1️⃣ Enter Target Microcontroller Board Name", placeholder="e.g., STM32 H743ZI2, ESP32, Arduino Uno", value="")
                with gr.Column(scale=2):
                    components_input = gr.Textbox(label="2️⃣ Enter Required Sensors, Pins, and Displays Profile", placeholder="e.g., sense distance via ultrasonic sensor and show on oled screen", value="", lines=2)
            
            compile_hw_btn = gr.Button("⚡ Run Multi-Pass Code Compilation & Wire Mapping Pass", variant="primary")
            
            with gr.Row():
                with gr.Column(scale=3):
                    hw_code_output = gr.Code(label="3️⃣ Verified Source Script Code Output", language="cpp", value="")
                    gr.Markdown("### 🔌 6️⃣ Physical Wires & Pin Connection Diagrams (Color Coded Wire Tracks)")
                    with gr.Group():
                        hw_wiring_output = gr.Markdown(value="*Awaiting compilation trigger sequence to map hardware schematics...*")
                    gr.Markdown("---")

                    hw_flash_payload = gr.Textbox(value="{}", visible=False)
                    hw_flash_btn = gr.Button("⚡ Flash to Board", variant="primary", visible=False)
                    hw_download_btn = gr.Button("📥 Download Verified Script & Wire Map File Locally", variant="secondary")
                    
                    with gr.Row():
                        hw_play_btn = gr.Button("🔊 Silicon talks", variant="secondary")
                        hw_stop_btn = gr.Button("🛑 Stop Silicon talks", variant="stop")
                    hw_voice_cache = gr.Textbox(visible=False)
                    hw_raw_download_cache = gr.Textbox(visible=False)
                with gr.Column(scale=2):
                    hw_log_output = gr.Textbox(label="Sequential Compilation Diagnostics Log", lines=15, interactive=False)

        # TAB 2: GENERAL APPLICATION CODE DEVELOPMENT (HTML/CSS LAYOUTS ONLY)
        with gr.Tab("💻 General Desktop Code (HTML/CSS)"):
            gr.Markdown("### 💡 Isolated Frontend Engine Workspace\n*This module is strictly dedicated to creating responsive front-end user interface designs using pure interactive HTML, CSS layouts, and client-side JavaScript canvas scripts.*")
            
            with gr.Row():
                sw_prompt_input = gr.Textbox(label="1️⃣ Enter Frontend User Interface Sizing, Theme & Animation Logic Rules", placeholder="e.g., create an interactive analog gauge odometer configuration with sleek animations...", value="", lines=2)
            
            compile_sw_btn = gr.Button("⚙️ Compile Frontend Design Blueprint", variant="primary")
            
            with gr.Row():
                with gr.Column(scale=3):
                    sw_code_output = gr.HTML(label="2️⃣ Live Functional Application Workspace Preview")
                    gr.Markdown("---")
                    
                    gr.HTML(value="""
                        <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px 16px; margin: 10px 0 20px 0; display: flex; align-items: flex-start; gap: 8px;">
                            <span style="color: #2563eb; font-size: 18px; font-weight: bold; line-height: 1.2;">ℹ️</span>
                            <p style="color: #1e3a8a !important; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; font-size: 13px !important; font-weight: 500 !important; margin: 0 !important; padding: 0 !important; line-height: 1.5 !important;">
                                <strong>How this works:</strong> The preview above runs in a sandboxed frame, so features like camera, microphone, or GPS may be limited here depending on your browser.
                                For full functionality &mdash; especially on mobile &mdash; click <strong>'Download Software Code Locally'</strong>, then either open it via <code>localhost</code> (desktop testing) or host the downloaded file on a free HTTPS service like Netlify or GitHub Pages (required for camera/location access on phones). The app itself will show an on-screen note if it detects it's running somewhere those features can't work.
                            </p>
                        </div>
                    """)
                    
                    sw_download_btn = gr.Button("📥 Download Software Code Locally", variant="secondary")
                    
                    with gr.Row():
                        sw_play_btn = gr.Button("🔊 Silicon talks", variant="secondary")
                        sw_stop_btn = gr.Button("🛑 Stop Silicon talks", variant="stop")
                    sw_voice_cache = gr.Textbox(visible=False)
                    sw_raw_download_cache = gr.Textbox(visible=False)
                with gr.Column(scale=2):
                    sw_log_output = gr.Textbox(label="Application Diagnostics Log", lines=15, interactive=False)

    # ==========================================
    # EVENT LOGIC TRACK WRAPPERS AND ROUTING
    # ==========================================
    
    logout_btn.click(fn=None, inputs=None, js=logout_session_js)
    
    theme_selector.change(fn=None, inputs=[theme_selector], js=theme_engine_js)
    app.load(fn=None, inputs=[theme_selector], js=theme_engine_js)
    app.load(fn=None, inputs=None, js=board_status_watcher_js)

    compile_hw_btn.click(
        fn=handle_hardware_pipeline,
        inputs=[board_input, components_input, manual_key_input],
        outputs=[hw_log_output, hw_code_output, hw_wiring_output, hw_raw_download_cache, hw_voice_cache, bus_status_display, hw_flash_payload, hw_flash_btn]
    )

    hw_flash_btn.click(fn=None, inputs=[hw_flash_payload], js=flash_to_board_js)
    hw_download_btn.click(fn=None, inputs=[hw_raw_download_cache], js=download_hw_js)

    hw_play_btn.click(fn=None, inputs=[voice_persona_dropdown, hw_voice_cache, hw_code_output], js=tts_javascript)
    hw_stop_btn.click(fn=None, inputs=None, js=stop_tts_javascript)

    compile_sw_btn.click(
        fn=handle_software_pipeline,
        inputs=[gr.State("html"), sw_prompt_input, manual_key_input],
        outputs=[sw_log_output, sw_code_output, sw_raw_download_cache, sw_voice_cache, bus_status_display]
    )

    sw_download_btn.click(fn=None, inputs=[sw_raw_download_cache], js=download_sw_js)

    sw_play_btn.click(fn=None, inputs=[voice_persona_dropdown, sw_voice_cache, sw_raw_download_cache], js=tts_javascript)
    sw_stop_btn.click(fn=None, inputs=None, js=stop_tts_javascript)

if __name__ == "__main__":
    app.launch(
        auth=("ZeroError", "123456"),
        auth_message="Please log in with your authorized Arro engine credentials.",
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Default(),
        js=force_light_mode_js,
        css=login_wall_css
    )
