# theme_engine.py

force_light_mode_js = """
() => {
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
}
"""

# Premium custom login card layout configurations
login_wall_css = """
/* Smooth subtle grid pattern background for the login wall */
.gradio-container-auth {
    background-color: #f1f5f9 !important;
    background-image: radial-gradient(#e2e8f0 1.5px, transparent 1.5px) !important;
    background-size: 24px 24px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 100vh !important;
    padding: 20px !important;
}

/* Elevate the default login card surface wrapper box */
.gradio-container-auth > div:first-child {
    border: 1px solid #e2e8f0 !important;
    background: #ffffff !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05) !important;
    border-radius: 16px !important;
    padding: 32px !important;
    max-width: 440px !important;
    width: 100% !important;
}

/* Clean typography styling rules for the headings */
.gradio-container-auth h2 {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 6px !important;
    text-align: center !important;
}

/* Subtitle message descriptive text */
.gradio-container-auth p {
    color: #64748b !important;
    font-size: 14px !important;
    margin-bottom: 24px !important;
    text-align: center !important;
}

/* Modernize input boundary boxes */
.gradio-container-auth input[type="text"], 
.gradio-container-auth input[type="password"] {
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    transition: all 0.2s ease !important;
}

/* Active focus transition ring mapping for login fields */
.gradio-container-auth input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.15) !important;
}

/* Primary login interactive submission button block */
.gradio-container-auth button {
    background-color: #f97316 !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 6px -1px rgba(249, 115, 22, 0.2) !important;
    width: 100% !important;
    margin-top: 12px !important;
}

.gradio-container-auth button:hover {
    background-color: #ea580c !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 12px -1px rgba(249, 115, 22, 0.3) !important;
}

@media (max-width: 768px) {
    .gradio-container-auth > div:first-child {
        padding: 24px 16px !important;
        margin: 10px !important;
    }
}
"""

theme_engine_js = """
(theme_name) => {
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
    
    let oldStyleBlock = document.getElementById("arro-custom-theme-layer");
    if (oldStyleBlock) { oldStyleBlock.remove(); }
    
    // Inject and cache the global HTML5 loading audio player container
    let dynamicAudioNode = document.getElementById("arro-loading-sfx-node");
    if (!dynamicAudioNode) {
        dynamicAudioNode = document.createElement("audio");
        dynamicAudioNode.id = "arro-loading-sfx-node";
        dynamicAudioNode.src = "/file=loading.mp3"; 
        dynamicAudioNode.loop = true; 
        dynamicAudioNode.volume = 0.5; 
        document.body.appendChild(dynamicAudioNode);
    }
    
    let primaryColor = "#f97316"; 
    let primaryHover = "#ea580c";
    let blockBg = "#ffffff";
    let bodyBg = "#f8fafc";
    let borderColor = "#cbd5e1";
    let labelColor = "#334155";
    let loaderColor = "#0284c7";
    
    if (theme_name.includes("Ocean")) {
        primaryColor = "#0284c7"; primaryHover = "#0369a1"; blockBg = "#f0f9ff"; bodyBg = "#e0f2fe"; borderColor = "#bae6fd"; labelColor = "#0369a1"; loaderColor = "#0284c7";
    } else if (theme_name.includes("Forest")) {
        primaryColor = "#16a34a"; primaryHover = "#15803d"; blockBg = "#f0fdf4"; bodyBg = "#dcfce7"; borderColor = "#bbf7d0"; labelColor = "#15803d"; loaderColor = "#16a34a";
    } else if (theme_name.includes("Sunset")) {
        primaryColor = "#ea580c"; primaryHover = "#c2410c"; blockBg = "#fff7ed"; bodyBg = "#ffedd5"; borderColor = "#fed7aa"; labelColor = "#9a3412"; loaderColor = "#ea580c";
    } else if (theme_name.includes("Steel")) {
        primaryColor = "#4b5563"; primaryHover = "#374151"; blockBg = "#f9fafb"; bodyBg = "#f3f4f6"; borderColor = "#e5e7eb"; labelColor = "#1f2937"; loaderColor = "#4b5563";
    }
    
    let cssRules = `
        body, .gradio-container { background-color: ${bodyBg} !important; }
        .gr-box, .gr-form, textarea, input, .gr-panel, div[class*="gr-"] { 
            background-color: ${blockBg} !important; 
            border-color: ${borderColor} !important; 
        }
        label span { color: ${labelColor} !important; font-weight: 600 !important; }
        button.primary { background-color: ${primaryColor} !important; border-color: ${primaryColor} !important; color: white !important; }
        button.primary:hover { background-color: ${primaryHover} !important; }

        /* ========================================================
           CROSS-PLATFORM AUTOMATIC ADAPTIVE LAYOUT
           ======================================================== */
        @media (max-width: 768px) {
            .form, [class*="gr-row"] {
                flex-direction: column !important;
                gap: 12px !important;
            }
            
            div[style*="flex-grow"], .block {
                flex-grow: 1 !important;
                width: 100% !important;
                max-width: 100% !important;
            }
            
            input, textarea, select {
                font-size: 14px !important;
            }
        }

        /* ========================================================
           CUSTOM LOADING SYMBOL OVERRIDE MATRIX
           ======================================================== */
        div[class*="loading"] svg, .wrap[class*="loading"] svg, .generating svg {
            display: none !important;
        }
        
        div[class*="loading"]::after, .wrap[class*="loading"]::after, .generating::after {
            content: "" !important;
            display: inline-block !important;
            width: 28px !important;
            height: 28px !important;
            border: 3px solid ${borderColor} !important;
            border-top-color: ${loaderColor} !important;
            border-radius: 50% !important;
            animation: arroSpinnerKeyframe 0.75s linear infinite !important;
            margin: 10px auto !important;
            position: absolute !important;
            top: 40% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 9999 !important;
        }

        @keyframes arroSpinnerKeyframe {
            to { transform: translate(-50%, -50%) rotate(360deg); }
        }

        /* ========================================================
           UI POLISH: SPACING & CARD STYLING
           ======================================================== */
        .gr-group {
            border-radius: 12px !important;
        }

        .tabs > .tab-nav {
            gap: 4px !important;
            border-bottom: 2px solid ${borderColor} !important;
        }

        .tabs > .tab-nav button {
            border-radius: 8px 8px 0 0 !important;
            font-weight: 600 !important;
            padding: 10px 18px !important;
        }

        .tabs > .tab-nav button.selected {
            color: ${primaryColor} !important;
            border-bottom: 2px solid ${primaryColor} !important;
        }

        #header-bar-container {
            padding-bottom: 12px !important;
            border-bottom: 1px solid ${borderColor} !important;
            margin-bottom: 16px !important;
        }

        button.secondary, button.stop {
            border-radius: 8px !important;
            font-weight: 600 !important;
        }

        .block, .form {
            border-radius: 10px !important;
        }

        @media (max-width: 768px) {
            .gr-row, [class*="gr-row"] {
                gap: 16px !important;
            }
            #header-bar-container {
                text-align: center !important;
            }
        }
    `;
    
    let styleElement = document.createElement("style");
    styleElement.id = "arro-custom-theme-layer";
    styleElement.innerHTML = cssRules;
    document.head.appendChild(styleElement);
}
"""

stop_sfx_js = """
() => {
    let sfx = document.getElementById("arro-loading-sfx-node");
    if (sfx) { sfx.pause(); sfx.currentTime = 0; }
}
"""
