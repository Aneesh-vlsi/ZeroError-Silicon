# app.py
import gradio as gr
import requests
from app_logic import handle_hardware_pipeline, handle_software_pipeline
from theme_engine import theme_engine_js, force_light_mode_js, stop_sfx_js, login_wall_css
from voice_engine import tts_javascript, stop_tts_javascript

# 🌐 YOUR VERIFIED SHEETDB API URL ENDPOINT LINK
DB_API_URL = "https://sheetdb.io/api/v1/t7s7ew3vcwp2r"

def fetch_all_users():
    """Queries the Google Sheet database to retrieve registered users safely."""
    try:
        response = requests.get(DB_API_URL, timeout=5)
        if response.status_code == 200:
            user_data_list = response.json()
            return {str(user.get('username', '')).strip(): str(user.get('password', '')).strip() for user in user_data_list if 'username' in user}
    except Exception:
        pass
    return {"ZeroError": "123456"}

def process_login(username, password):
    """Verifies user credentials dynamically against the Google Sheets layer."""
    username_clean = str(username).strip()
    password_clean = str(password).strip()
    
    if not username_clean or not password_clean:
        return gr.update(visible=True), gr.update(visible=False), "❌ Input parameters cannot be left blank."
        
    registered_users = fetch_all_users()
    
    if username_clean in registered_users and registered_users[username_clean] == password_clean:
        return gr.update(visible=False), gr.update(visible=True), ""
    return gr.update(visible=True), gr.update(visible=False), "❌ Invalid credentials. Please try again."

def process_signup(username, password, confirm_password):
    """Registers a brand new user into the Google Sheet."""
    username_clean = str(username).strip()
    password_clean = str(password).strip()
    confirm_clean = str(confirm_password).strip()
    
    if not username_clean or not password_clean:
        return "❌ Input parameters cannot be empty."
    if len(username_clean) < 3:
        return "❌ Username must be at least 3 characters."
    if password_clean != confirm_clean:
        return "❌ Passwords do not match."
        
    current_users = fetch_all_users()
    if username_clean in current_users:
        return "❌ Username already exists."
        
    payload = {"data": [{"username": username_clean, "password": password_clean}]}
    
    try:
        response = requests.post(DB_API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            return "🎉 Account created successfully! Please go to the Sign In tab."
    except Exception as e:
        return f"❌ Registration failed: {str(e)}"
    return "❌ Database connection error."

def process_logout():
    """Logs out the user and brings back the login screen."""
    return gr.update(visible=True), gr.update(visible=False), "", ""

# Custom client-side download logic
download_hw_js = """
(file_content) => {
    if (!file_content || file_content.trim() === "") {
        alert("Attention: No compiled blueprint data available to export yet.");
        return;
    }
    let customName = prompt("Enter a filename for your hardware blueprint:", "verified_embedded_blueprint.txt");
    if (!customName) return; 
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
        alert("Attention: No compiled software asset data available to export yet.");
        return;
    }
    let customName = prompt("Enter a filename for your software code:", "compiled_application.html");
    if (!customName) return; 
    let dataBlob = new Blob([file_content], { type: "text/html;charset=utf-8" });
    let linkElement = document.createElement("a");
    linkElement.href = URL.createObjectURL(dataBlob);
    linkElement.download = customName;
    document.body.appendChild(linkElement);
    linkElement.click();
    document.body.removeChild(linkElement);
}
"""

def live_sync_buffer(val): return val

with gr.Blocks() as app:

    
    # -------------------------------------------------------------------------
    # AUTH PANEL CONTAINER (LOGIN & SIGNUP CORES)
    # -------------------------------------------------------------------------
    with gr.Column(elem_id="auth_panel", visible=True) as auth_panel:
        gr.Markdown("## 🔒 ZeroError Silicon Gateway")
        
        with gr.Tabs():
            with gr.Tab("Sign In Workspace"):
                login_user = gr.Textbox(label="Username Token ID", placeholder="Enter username...")
                login_pass = gr.Textbox(label="Security Password Pin", type="password", placeholder="Enter password...")
                login_btn = gr.Button("Authorize and Launch Canvas Engine", variant="primary")
                login_error = gr.Markdown(value="")
                
            with gr.Tab("Create Secure Profile"):
                signup_user = gr.Textbox(label="Assign Workspace Username ID", placeholder="Min 3 characters...")
                signup_pass = gr.Textbox(label="Create Access Password Track", type="password", placeholder="Choose password...")
                signup_confirm = gr.Textbox(label="Verify Password Track Confirmation", type="password", placeholder="Retype password...")
                signup_btn = gr.Button("Provision Free Account Hub Instance", variant="secondary")
                signup_status = gr.Markdown(value="")

    # -------------------------------------------------------------------------
    # MAIN WORKSPACE CONTAINER (RESTORED DUAL-TAB SYSTEM)
    # -------------------------------------------------------------------------
    with gr.Column(visible=False) as workspace_panel:
        gr.Markdown("# 🤖 ZeroError Silicon")
        gr.Markdown("<p style='color: #475569 !important; margin-bottom: 16px !important;'>Next-Generation AI Tooling for Heterogeneous Microcontrollers</p>")
        
        with gr.Row():
            bus_status_display = gr.Textbox(label="Hardware Bus Tracking Status", value="Status: Workspace Online. Ready to receive design rules.", interactive=False, scale=3)
            theme_selector = gr.Dropdown(
                label="🎨 Select Interface Workspace Theme",
                choices=["Light Slate (Default Clean)", "Ocean Blue Breeze", "Forest Mint", "Sunset Orange & Ember", "Classic Steel Cyber"],
                value="Light Slate (Default Clean)",
                scale=2
            )
            logout_btn = gr.Button("🚪 Log Out", variant="stop", scale=1)

        with gr.Row():
            voice_persona_dropdown = gr.Dropdown(label="🗣️ Select Assistant Voice Profile Persona (Global Control)", choices=["Max (Standard Male Profile)", "May (Clear Female Profile)", "Heera (Indian Accent Female)", "Jimmy (Fast Tech Profile)"], value="Max (Standard Male Profile)", interactive=True)
            manual_key_input = gr.Textbox(label="🔑 Emergency API Token Manual Override (Optional)", placeholder="Paste fresh AQ.Ab8... token here...", type="password", interactive=True)

        with gr.Tabs():
            # TAB 1: EMBEDDED HARDWARE FIRMWARE
            with gr.Tab("📟 Embedded Hardware Firmware"):
                gr.Markdown("### Secure Microcontroller Code & Wiring Synthesis Block")
                with gr.Row():
                    board_input = gr.Textbox(label="1️⃣ Enter Target Microcontroller Board Name", placeholder="e.g., STM32 H743ZI2, ESP32")
                    components_input = gr.Textbox(label="2️⃣ Enter Required Sensors Profile", placeholder="e.g., sense distance via ultrasonic sensor", lines=2)
                
                compile_hw_btn = gr.Button("⚡ Run Multi-Pass Code Compilation & Wire Mapping Pass", variant="primary")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        hw_code_output = gr.Code(label="3️⃣ Verified Source Script Code Output", language="cpp", value="")
                        gr.Markdown("### 🔌 Physical Wires & Pin Connection Diagrams (Color Coded Wire Tracks)")
                        hw_wiring_output = gr.Markdown(value="*Awaiting compilation trigger sequence to map hardware schematics...*")
                        gr.Markdown("---")
                        hw_download_btn = gr.Button("📥 Download Verified Script & Wire Map File Locally", variant="secondary")
                        with gr.Row():
                            hw_play_btn = gr.Button("🔊 Silicon talks", variant="secondary")
                            hw_stop_btn = gr.Button("🛑 Stop Silicon talks", variant="stop")
                        hw_voice_cache = gr.Textbox(visible=False)
                        hw_raw_download_cache = gr.Textbox(visible=False)
                    with gr.Column(scale=2):
                        hw_log_output = gr.Textbox(label="Sequential Compilation Diagnostics Log", lines=15, interactive=False)

                      # TAB 2: GENERAL APPLICATION CODE DEVELOPMENT (HTML/CSS)
            with gr.Tab("💻 General Desktop Code (HTML/CSS)"):
                gr.Markdown("### 💡 Isolated Frontend Engine Workspace\n*This module is strictly dedicated to creating responsive front-end user interface designs using pure interactive HTML, CSS layouts, and client-side JavaScript canvas scripts.*")
                
                with gr.Row():
                    sw_prompt_input = gr.Textbox(label="1️⃣ Enter Frontend User Interface Sizing, Theme & Animation Logic Rules", placeholder="e.g., sleek gauge odometer animations...", value="", lines=2)
                
                compile_sw_btn = gr.Button("⚙️ Compile Frontend Design Blueprint", variant="primary")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        sw_code_output = gr.HTML(label="2️⃣ Live Functional Application Workspace Preview")
                        gr.Markdown("---")
                        
                        gr.HTML(value="""
                            <div style="background-color: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; padding: 12px 16px; margin: 10px 0 20px 0; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #dc2626; font-size: 18px; font-weight: bold; line-height: 1;">⚠️</span>
                                <p style="color: #991b1b !important; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; font-size: 13px !important; font-weight: 600 !important; margin: 0 !important; padding: 0 !important; line-height: 1.4 !important;">
                                    Notice: Interactive phone hardware elements are restricted inside this embedded preview area. Kindly click 'Download Software Code Locally' below to launch the functional app inside your standalone browser.
                                </p>
                            </div>
                        """)
                        
                        sw_download_btn = gr.Button("📥 Download Software Code Locally", variant="secondary")
                        
                        with gr.Row():
                            sw_play_btn = gr.Button("🔊 Silicon talks", variant="secondary")
                            sw_stop_btn = gr.Button("🛑 Stop Application Voice Explanation", variant="stop")
                        sw_voice_cache = gr.Textbox(visible=False)
                        sw_raw_download_cache = gr.Textbox(visible=False)
                    with gr.Column(scale=2):
                        sw_log_output = gr.Textbox(label="Software Asset Compilation Diagnostics Log", lines=15, interactive=False)

    # -------------------------------------------------------------------------
    # ROUTING LOGIC PIPELINES (RECONNECTED EVENT LOGIC)
    # -------------------------------------------------------------------------
    login_btn.click(
        fn=process_login,
        inputs=[login_user, login_pass],
        outputs=[auth_panel, workspace_panel, login_error]
    )
    
    signup_btn.click(
        fn=process_signup,
        inputs=[signup_user, signup_pass, signup_confirm],
        outputs=[signup_status]
    )
    
    logout_btn.click(
        fn=process_logout,
        inputs=None,
        outputs=[auth_panel, workspace_panel, login_user, login_pass]
    )

    board_input.blur(fn=live_sync_buffer, inputs=[board_input], outputs=[board_input])
    components_input.blur(fn=live_sync_buffer, inputs=[components_input], outputs=[components_input])
    sw_prompt_input.blur(fn=live_sync_buffer, inputs=[sw_prompt_input], outputs=[sw_prompt_input])
    
    theme_selector.change(fn=None, inputs=[theme_selector], outputs=None, js=theme_engine_js)
    
    # Reconnected Hardware Actions
    compile_hw_btn.click(
        fn=handle_hardware_pipeline,
        inputs=[board_input, components_input, manual_key_input],
        outputs=[hw_log_output, hw_code_output, hw_wiring_output, hw_raw_download_cache, hw_voice_cache, bus_status_display]
    ).then(fn=None, inputs=None, outputs=None, js=stop_sfx_js)
    
    hw_download_btn.click(fn=None, inputs=[hw_raw_download_cache], outputs=None, js=download_hw_js)
    hw_play_btn.click(fn=None, inputs=[voice_persona_dropdown, hw_voice_cache, hw_code_output], outputs=None, js=tts_javascript)
    hw_stop_btn.click(fn=None, inputs=None, outputs=None, js=stop_tts_javascript)

    # Reconnected Software Actions
    compile_sw_btn.click(
        fn=handle_software_pipeline,
        inputs=[gr.Textbox(value="HTML/JavaScript Canvas UI", visible=False), sw_prompt_input, manual_key_input],
        outputs=[sw_log_output, sw_code_output, sw_raw_download_cache, sw_voice_cache, bus_status_display]
    ).then(fn=None, inputs=None, outputs=None, js=stop_sfx_js)
    
    sw_download_btn.click(fn=None, inputs=[sw_raw_download_cache], outputs=None, js=download_sw_js)
    sw_play_btn.click(fn=None, inputs=[voice_persona_dropdown, sw_voice_cache, sw_code_output], outputs=None, js=tts_javascript)
    sw_stop_btn.click(fn=None, inputs=None, outputs=None, js=stop_tts_javascript)

app.title = "Complex Hardware AI Engine"

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Default(),
        js=force_light_mode_js,
        css=login_wall_css       # 👈 PLACED SECURELY HERE FOR GRADIO 6.0 compatibility
    )
