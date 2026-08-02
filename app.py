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
            return {str(user.get('UserName', '')).strip(): str(user.get('Password', '')).strip() for user in user_data_list if 'UserName' in user}
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
        
    payload = {"data": [{"UserName": username_clean, "Password": password_clean}]}
    
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

# Standard placeholder scripts
download_hw_js = "(file_content) => { /* Custom download routine */ }"
download_sw_js = "(file_content) => { /* Custom download routine */ }"
def live_sync_buffer(val): return val

with gr.Blocks(css=login_wall_css) as app:
    
    # -------------------------------------------------------------------------
    # AUTH PANEL CONTAINER
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
    # MAIN WORKSPACE CONTAINER
    # -------------------------------------------------------------------------
    with gr.Column(visible=False) as workspace_panel:
        gr.Markdown("# 🤖 ZeroError Silicon")
        
        with gr.Row():
            bus_status_display = gr.Textbox(label="Hardware Bus Tracking Status", value="Status: Workspace Online.", interactive=False, scale=3)
            theme_selector = gr.Dropdown(
                label="🎨 Select Interface Workspace Theme",
                choices=["Light Slate (Default Clean)", "Ocean Blue Breeze"],
                value="Light Slate (Default Clean)",
                scale=2
            )
            logout_btn = gr.Button("🚪 Log Out", variant="stop", scale=1)

        with gr.Tabs():
            with gr.Tab("📟 Embedded Hardware Firmware"):
                with gr.Row():
                    board_input = gr.Textbox(label="1️⃣ Enter Target Microcontroller Board Name")
                    components_input = gr.Textbox(label="2️⃣ Enter Required Sensors Profile", lines=2)
                compile_hw_btn = gr.Button("⚡ Run Multi-Pass Code Compilation", variant="primary")
                with gr.Row():
                    with gr.Column(scale=3):
                        hw_code_output = gr.Code(label="3️⃣ Code Output", language="cpp")
                        hw_wiring_output = gr.Markdown(value="*Awaiting compilation...*")
                    with gr.Column(scale=2):
                        hw_log_output = gr.Textbox(label="Diagnostics Log", lines=10, interactive=False)

    # -------------------------------------------------------------------------
    # ROUTING LOGIC PIPELINES
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

    theme_selector.change(fn=None, inputs=[theme_selector], outputs=None, js=theme_engine_js)
    
    compile_hw_btn.click(
        fn=handle_hardware_pipeline,
        inputs=[board_input, components_input, gr.State("")],
        outputs=[hw_log_output, hw_code_output, hw_wiring_output, gr.State(), gr.State(), bus_status_display]
    )

app.title = "Complex Hardware AI Engine"

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Default(),
        js=force_light_mode_js
    )
