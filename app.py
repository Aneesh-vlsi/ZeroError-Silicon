import gradio as gr
import requests
from app_logic import handle_hardware_pipeline, handle_software_pipeline
from theme_engine import theme_engine_js, force_light_mode_js, stop_sfx_js, login_wall_css
from voice_engine import tts_javascript, stop_tts_javascript

# 🌐 YOUR VERIFIED SHEETDB API URL ENDPOINT LINK
DB_API_URL = "https://sheetdb.io"

def fetch_all_users():
    """Queries the Google Sheet database to retrieve registered users safely."""
    try:
        response = requests.get(DB_API_URL, timeout=5)
        if response.status_code == 200:
            user_data_list = response.json()
            # Formats list array objects into a swift lookup dictionary matrix
            return {user['UserName']: user['Password'] for user in user_data_list if 'UserName' in user and 'Password' in user}
    except Exception:
        pass
    return {"ZeroError": "123456"} # Resilient hardcoded failover account

def process_login(username, password):
    """Verifies user credentials dynamically against the Google Sheets layer."""
    username_clean = str(username).strip()
    password_clean = str(password).strip()
    
    if not username_clean or not password_clean:
        return gr.update(visible=True), gr.update(visible=False), "❌ Input parameters cannot be left blank."
        
    registered_users = fetch_all_users()
    
    if username_clean in registered_users and str(registered_users[username_clean]) == password_clean:
        return gr.update(visible=False), gr.update(visible=True), ""
    return gr.update(visible=True), gr.update(visible=False), "❌ Invalid entry tracking credentials or user registry block."

def process_signup(username, password, confirm_password):
    """Registers a brand new customer node directly into the cloud Google Sheet matrix."""
    username_clean = str(username).strip()
    password_clean = str(password).strip()
    confirm_clean = str(confirm_password).strip()
    
    if not username_clean or not password_clean:
        return "❌ Input parameters cannot be unpopulated."
    if len(username_clean) < 3:
        return "❌ Username parameter string length must be at least 3 characters."
    if password_clean != confirm_clean:
        return "❌ Confirmation mismatch. Passwords do not cross-verify."
        
    current_users = fetch_all_users()
    if username_clean in current_users:
        return "❌ Security Block: Username token is already active in our database registry."
        
    # Compile raw payload structure matching your exact Google Sheet headers
    payload = {"data": [{"UserName": username_clean, "Password": password_clean}]}
    
    try:
        response = requests.post(DB_API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            return "🎉 Account provisioned successfully! Kindly navigate back to the Sign In panel view frame to access your terminal tools."
    except Exception as e:
        return f"❌ Cloud Sync Failure Hook: {str(e)}"
    return "❌ Registration transaction aborted due to database pipeline connection error."

# Existing custom client scripts
download_hw_js = "(file_content) => { /* Hardware handler */ }"
download_sw_js = "(file_content) => { /* Software handler */ }"
def live_sync_buffer(val): return val

with gr.Blocks(css=login_wall_css) as app:
    # -------------------------------------------------------------------------
    # AUTHENTICATION CONTAINER (DYNAMIC SIGNUP & LOGIN WALLS)
    # -------------------------------------------------------------------------
    with gr.Column(elem_id="auth_panel") as auth_panel:
        gr.Markdown("## 🔒 ZeroError Silicon Enterprise Gateway")
        gr.Markdown("Welcome. Please sign in with your enterprise credentials or create a secure workspace account profile node below.")
        
        with gr.Tabs():
            with gr.Tab("Sign In Workspace"):
                login_user = gr.Textbox(label="Username Token ID", placeholder="Enter your identity key...")
                login_pass = gr.Textbox(label="Security Password Pin", type="password", placeholder="Enter your credential password string...")
                login_btn = gr.Button("Authorize and Launch Canvas Engine", variant="primary")
                login_error = gr.Markdown(value="")
                
            with gr.Tab("Create Secure Profile"):
                signup_user = gr.Textbox(label="Assign Workspace Username ID", placeholder="Min 3 characters, alphanumeric...")
                signup_pass = gr.Textbox(label="Create Access Password Track", type="password", placeholder="Choose an encrypted profile string...")
                signup_confirm = gr.Textbox(label="Verify Password Track Confirmation", type="password", placeholder="Re-enter access string parameter...")
                signup_btn = gr.Button("Provision Free Account Hub Instance", variant="secondary")
                signup_status = gr.Markdown(value="")

    # -------------------------------------------------------------------------
    # MAIN INDUSTRIAL ENGINE WORKSPACE (Initially Hidden Until Authorized)
    # -------------------------------------------------------------------------
    with gr.Column(visible=False) as workspace_panel:
        gr.Markdown("# 🤖 ZeroError Silicon")
        gr.Markdown("<p style='color: #475569 !important;'>Next-Generation AI Tooling for Heterogeneous Microcontrollers</p>")
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
            voice_persona_dropdown = gr.Dropdown(label="🗣️ Select Assistant Voice Profile Persona (Global Control)", choices=["Max (Standard Male Profile)", "May (Clear Female Profile)"], value="Max (Standard Male Profile)", interactive=True)
            manual_key_input = gr.Textbox(label="🔑 Emergency API Token Manual Override (Optional)", placeholder="Paste fresh AQ.Ab8... token here...", type="password", interactive=True)

        with gr.Tabs():
            with gr.Tab("📟 Embedded Hardware Firmware"):
                gr.Markdown("### Secure Microcontroller Code & Wiring Synthesis Block")
                with gr.Row():
                    board_input = gr.Textbox(label="1️⃣ Enter Target Microcontroller Board Name", placeholder="e.g., STM32 H743ZI2, ESP32")
                    components_input = gr.Textbox(label="2️⃣ Enter Required Sensors, Pins, and Displays Profile", placeholder="e.g., sense distance via ultrasonic sensor", lines=2)
                compile_hw_btn = gr.Button("⚡ Run Multi-Pass Code Compilation & Wire Mapping Pass", variant="primary")
                with gr.Row():
                    with gr.Column(scale=3):
                        hw_code_output = gr.Code(label="3️⃣ Verified Source Script Code Output", language="cpp", value="")
                        hw_wiring_output = gr.Markdown(value="*Awaiting compilation trigger sequence to map hardware schematics...*")
                        hw_download_btn = gr.Button("📥 Download Verified Script & Wire Map File Locally", variant="secondary")
                        with gr.Row():
                            hw_play_btn = gr.Button("🔊 Silicon talks", variant="secondary")
                            hw_stop_btn = gr.Button("🛑 Stop Silicon talks", variant="stop")
                        hw_voice_cache = gr.Textbox(visible=False)
                        hw_raw_download_cache = gr.Textbox(visible=False)
                    with gr.Column(scale=2):
                        hw_log_output = gr.Textbox(label="Sequential Compilation Diagnostics Log", lines=15, interactive=False)

    # -------------------------------------------------------------------------
    # WORKSPACE SUBMISSION LINKAGE ENGINE MATRIX
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

    board_input.blur(fn=live_sync_buffer, inputs=[board_input], outputs=[board_input])
    components_input.blur(fn=live_sync_buffer, inputs=[components_input], outputs=[components_input])
    theme_selector.change(fn=None, inputs=[theme_selector], outputs=None, js=theme_engine_js)
    
    compile_hw_btn.click(
        fn=handle_hardware_pipeline,
        inputs=[board_input, components_input, manual_key_input],
        outputs=[hw_log_output, hw_code_output, hw_wiring_output, hw_raw_download_cache, hw_voice_cache, bus_status_display]
    ).then(fn=None, inputs=None, outputs=None, js=stop_sfx_js)

app.title = "Complex Hardware AI Engine"

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",   # Essential cloud host mapping
        server_port=7860,        # Render target web port config
        theme=gr.themes.Default(),
        js=force_light_mode_js
    )
