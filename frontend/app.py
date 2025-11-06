import streamlit as st
import requests
import json
import pandas as pd

from datetime import datetime

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        color: #1f4e79;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .step-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f4e79;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #b3d9ff;
        margin: 1rem 0;
    }
    .placeholder-card {
        background-color: white;
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
    .progress-info {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f4e79;
    }
    /* Hide Streamlit's default file uploader file list (redundant notification) */
    div[data-testid="stFileUploader"] ul[data-testid="stFileUploaderFileList"],
    div[data-testid="stFileUploader"] > div:has(ul),
    div[data-testid="stFileUploader"] ul {
        display: none !important;
    }
    /* Make all primary buttons green */
    button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }
    button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    button[kind="primary"]:focus {
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.5) !important;
    }
    /* Make download buttons green too */
    a[download] button[kind="primary"],
    div[data-testid="stDownloadButton"] button {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }
    a[download] button[kind="primary"]:hover,
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    </style>
""", unsafe_allow_html=True)

def validate_input(label: str, value: str, question: str = "") -> tuple[bool, str]:
    """
    Validate user input for specific placeholders (Date, State, Amount).
    Returns (is_valid, error_message)
    """
    label_upper = label.upper().strip()
    val = value.strip()

    # --- Date validation (MM/DD/YYYY) ---
    if "DATE" in label_upper:
        try:
            datetime.strptime(val, "%m/%d/%Y")
            return True, ""
        except ValueError:
            return False, "❌ Please enter the date in MM/DD/YYYY format (e.g., 03/14/2025)."

    # --- State validation (U.S. two-letter codes) ---
    if "STATE" in label_upper or "INCORPORATION" in label_upper:
        US_STATES = {
            "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY",
            "LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND",
            "OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
        }
        if val.upper() not in US_STATES:
            return False, "❌ Please enter a valid two-letter U.S. state abbreviation (e.g., MD, CA, NY)."
        return True, ""

    # --- Amount validation (for monetary values) ---
    amount_keywords = ["AMOUNT", "PRICE", "COST", "VALUATION", "CAP", "PAYMENT", "INVESTMENT", 
                       "PRINCIPAL", "DOLLAR", "DOLLARS", "MONEY", "PAY", "FEE", "$"]
    question_upper = question.upper() if question else ""
    # Check label or question for amount-related keywords
    is_amount_field = (
        any(keyword in label_upper for keyword in amount_keywords) or 
        label.startswith("$") or
        any(keyword in question_upper for keyword in amount_keywords)
    )
    
    if is_amount_field:
        # Remove common currency symbols and formatting
        cleaned = val.replace("$", "").replace(",", "").replace(" ", "").strip()
        
        # Check if it's a valid number (integer or decimal)
        try:
            # Try parsing as float to allow decimals
            num_val = float(cleaned)
            # Must be positive
            if num_val < 0:
                return False, "❌ Please enter a positive amount."
            # Check if it looks like a reasonable number (not just a dot)
            if cleaned == "." or cleaned == "":
                return False, "❌ Please enter a valid amount (e.g., 1000, 1,000, or 1000.50)."
            return True, ""
        except ValueError:
            return False, "❌ Please enter a valid amount as a number (e.g., 1000, 1,000, or 1000.50)."

    # Default: no validation
    return True, ""


# --- Streamlit Page Config ---
st.set_page_config(page_title="Lexsy Legal Assistant", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")


# ------------------- SIDEBAR -------------------
# API KEY INPUT SECTION
st.sidebar.header("🔑 OpenAI API Key")
st.sidebar.markdown(
    "To use the intelligent placeholder assistant, please enter your **OpenAI API key** below. "
    "It will be used temporarily during this session and **not stored anywhere**."
)

user_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
if user_api_key:
    st.session_state["api_key"] = user_api_key
    st.sidebar.success("✅ Key saved for this session.")
else:
    st.sidebar.warning("⚠️ You can still use the parsing and filling, but AI features require a key.")


# Header Section
st.markdown('<h1 class="main-header">⚖️ Lexsy AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Transform the way you prepare legal documents — from placeholder to polished in minutes</p>', unsafe_allow_html=True)

# Service Introduction Section
st.markdown("""
<div style="text-align: center; padding: 1rem 0 2rem 0; max-width: 800px; margin: 0 auto;">
    <p style="font-size: 1.1rem; color: #666; line-height: 1.6;">
        Streamline your document workflow with AI.
        Upload your draft, let Lexsy detect placeholders, and fill them conversationally with smart validation — while keeping your original format intact.
    </p>
</div>
""", unsafe_allow_html=True)

# Feature Highlights
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 10px; height: 150px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
        <div style="font-weight: 600; color: #1f4e79; margin-bottom: 0.25rem;">AI-Powered Detection</div>
        <div style="font-size: 0.9rem; color: #666;">Automatically identifies placeholders</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 10px; height: 150px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
        <div style="font-weight: 600; color: #1f4e79; margin-bottom: 0.25rem;">Natural Conversation</div>
        <div style="font-size: 0.9rem; color: #666;">Intuitive form interface</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 10px; height: 150px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
        <div style="font-weight: 600; color: #1f4e79; margin-bottom: 0.25rem;">Smart Validation</div>
        <div style="font-size: 0.9rem; color: #666;">Real-time input validation</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 10px; height: 150px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📄</div>
        <div style="font-weight: 600; color: #1f4e79; margin-bottom: 0.25rem;">Format Preservation</div>
        <div style="font-size: 0.9rem; color: #666;">Maintains original .docx styling</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Backend URL ---
#BACKEND_URL = "http://127.0.0.1:8000"  # Local backend
BACKEND_URL = "https://lexsy-ai-swe-backend.onrender.com"  # Production backend 

def send_request_with_auth(endpoint, **kwargs):
    """Helper to attach API key if available."""
    headers = {}
    if "api_key" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['api_key']}"
    return requests.post(f"{BACKEND_URL}/{endpoint}", headers=headers, **kwargs)



# --- Initialize session state ---
st.session_state.setdefault("placeholders", [])
st.session_state.setdefault("responses", {})
st.session_state.setdefault("current_index", 0)
st.session_state.setdefault("conversation_started", False)
st.session_state.setdefault("doc_bytes", None)
st.session_state.setdefault("doc_name", None)
st.session_state.setdefault("questions_initialized", False)
st.session_state.setdefault("placeholder_questions", {})  # occ_id -> question text
st.session_state.setdefault("user_inputs", {})  # occ_id -> user input value
st.session_state.setdefault("validation_errors", {})  # occ_id -> error message
st.session_state.setdefault("extraction_complete", False)
st.session_state.setdefault("review_mode", False)

# ========== STEP 1: DOCUMENT UPLOAD ==========
st.markdown("### 📤 Step 1: Upload Document")

uploaded_file = st.file_uploader(
    "Choose a `.docx` file to process",
    type=["docx"],
    help="Upload your legal document template with placeholders",
    key="file_uploader"
)

# Display uploaded file name in the highlighted space
uploaded_file_name = ""
if uploaded_file:
    uploaded_file_name = uploaded_file.name
elif st.session_state.get("doc_name"):
    uploaded_file_name = st.session_state.get("doc_name", "")

if uploaded_file_name:
    st.markdown(f'<div style="padding: 0.75rem; background-color: #f0f0f0; border-radius: 5px; margin: 1rem 0; border-left: 4px solid #1f4e79;"><strong>📄 Uploaded:</strong> {uploaded_file_name}</div>', unsafe_allow_html=True)

if uploaded_file and not st.session_state.extraction_complete:
    col1, col2 = st.columns([3, 1])
    with col1:
        pass  # File name already shown above
    with col2:
        if st.button("🔍 Analyse", type="primary", use_container_width=True):
            st.session_state.extraction_button_clicked = True

if st.session_state.get("extraction_button_clicked", False) and uploaded_file:
    with st.spinner("🔄 Analysing document..."):
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        try:
            res = send_request_with_auth("parse_doc", files=files, timeout=60)
            if res.ok:
                data = res.json()
                
                # Save to session
                occs = list(data.get("occurrences", []))
                st.session_state.occurrences = occs
                st.session_state.context_map = data.get("context_map", {})
                st.session_state.responses_global = {}
                st.session_state.responses_occurrence = {}
                st.session_state.current_index = 0
                st.session_state.conversation_started = True
                st.session_state.doc_bytes = uploaded_file.getvalue()
                st.session_state.doc_name = uploaded_file.name
                st.session_state.questions_initialized = False
                st.session_state.placeholder_questions = {}
                st.session_state.user_inputs = {}
                st.session_state.validation_errors = {}
                st.session_state.extraction_complete = True
                st.session_state.extraction_button_clicked = False
                st.rerun()

            else:
                st.error(f"❌ Backend error: {res.status_code}")
        except Exception as e:
            st.error(f"❌ Request failed: {e}")
        st.session_state.extraction_button_clicked = False

# ========== STEP 2: FILL PLACEHOLDERS ==========
if st.session_state.extraction_complete and st.session_state.occurrences and not st.session_state.review_mode:
    st.markdown("### Please answer the following questions")
    
    occs = list(st.session_state.occurrences)
    
    # === Initialize questions for all placeholders ===
    if not st.session_state.questions_initialized:
        with st.spinner("🔄 Preparing questions for all placeholders..."):
            questions_map = {}
            for occ in occs:
                occ_id = occ["id"]
                label = occ["label"].upper()
                context = st.session_state.context_map.get(occ_id, "")
                prev_global = st.session_state.responses_global.get(label, "")
                prev_occ = st.session_state.responses_occurrence.get(occ_id, "")
                
                try:
                    init = send_request_with_auth(
                        "chat_fill",
                        data={
                            "placeholder": label,
                            "context": context,
                            "user_input": "",
                            "previous_global_value": prev_global,
                            "prior_occurrence_value": prev_occ,
                        },
                        timeout=60,
                    )
                    if init.ok:
                        ai0 = init.json()
                        action0 = ai0.get("action", "ask")
                        filled0 = ai0.get("filled_value", "").strip()
                        q0 = ai0.get("followup_question", "").strip()
                        
                        # Auto-fill if reuse or LLM can fill
                        if action0 == "reuse" and prev_global:
                            st.session_state.responses_occurrence[occ_id] = prev_global
                            questions_map[occ_id] = f"✅ Auto-filled (reused): **{prev_global}**"
                            if occ_id in st.session_state.user_inputs:
                                del st.session_state.user_inputs[occ_id]
                        elif action0 == "fill" and filled0:
                            st.session_state.responses_occurrence[occ_id] = filled0
                            if label not in st.session_state.responses_global:
                                st.session_state.responses_global[label] = filled0
                            questions_map[occ_id] = f"✅ Auto-filled: **{filled0}**"
                            if occ_id in st.session_state.user_inputs:
                                del st.session_state.user_inputs[occ_id]
                        else:
                            questions_map[occ_id] = q0 or f"Please provide the value for **{label}**."
                    else:
                        questions_map[occ_id] = f"Please provide the value for **{label}**."
                except Exception as e:
                    questions_map[occ_id] = f"Please provide the value for **{label}**."
            
            st.session_state.placeholder_questions = questions_map
            st.session_state.questions_initialized = True
            st.rerun()
    
    # === Display all placeholders with input fields ===
    total_count = len(occs)
    
    # First, calculate filled_count by checking all fields
    filled_count = 0
    validation_errors = st.session_state.get("validation_errors", {})
    for occ in occs:
        occ_id = occ["id"]
        user_input_key = f"input_{occ_id}"
        current_value = st.session_state.responses_occurrence.get(occ_id, "")
        question = st.session_state.placeholder_questions.get(occ_id, "")
        widget_val = st.session_state.get(user_input_key, "").strip()
        
        # Count as filled if auto-filled or has valid input without errors
        if current_value and "✅ Auto-filled" in question:
            filled_count += 1
        elif widget_val and occ_id not in validation_errors:
            # Double-check validation for filled fields
            label_upper = occ["label"].upper()
            valid, _ = validate_input(label_upper, widget_val, question)
            if valid:
                filled_count += 1
    
    # Progress indicator (compact)
    progress_ratio = filled_count / total_count if total_count > 0 else 0
    col1, col2 = st.columns([4, 1])
    with col1:
        st.progress(progress_ratio)
    with col2:
        st.markdown(f'<p class="progress-info" style="margin:0; padding-top:0.25rem;">{filled_count}/{total_count}</p>', unsafe_allow_html=True)
    
    # Placeholder cards
    for idx, occ in enumerate(occs):
        occ_id = occ["id"]
        label = occ["label"]
        context = st.session_state.context_map.get(occ_id, "")
        question = st.session_state.placeholder_questions.get(occ_id, f"Please provide **{label}**.")
        
        # Check if already auto-filled
        current_value = st.session_state.responses_occurrence.get(occ_id, "")
        is_auto_filled = current_value and "✅ Auto-filled" in question
        
        if is_auto_filled:
            st.markdown(f"**{idx + 1}. {label}**")
            st.caption(question)
            st.text_input(
                "Value",
                value=current_value,
                key=f"display_{occ_id}",
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            # Get user input for this field
            user_input_key = f"input_{occ_id}"
            label_upper = label.upper()
            
            # Check if there's a previous value for the same label (from earlier occurrences)
            previous_global_value = st.session_state.responses_global.get(label_upper, "")
            
            # Initialize widget value in session state if needed
            if user_input_key not in st.session_state:
                # Widget doesn't exist yet - initialize with global value if available
                if previous_global_value:
                    st.session_state[user_input_key] = previous_global_value
                    st.session_state.user_inputs[occ_id] = previous_global_value
                else:
                    st.session_state[user_input_key] = ""
            else:
                # Widget exists - check if we should update it with global value
                current_widget_val = st.session_state.get(user_input_key, "")
                # If widget is empty but we have a global value, prefill it
                if not current_widget_val and previous_global_value:
                    st.session_state[user_input_key] = previous_global_value
                    st.session_state.user_inputs[occ_id] = previous_global_value
            
            # Get the current value to display
            prev_input = st.session_state.get(user_input_key, "")
            
            st.markdown(f"**{idx + 1}. {label}**")
            st.caption(question)
            
            user_input = st.text_input(
                f"Enter your answer",
                value=prev_input,
                key=user_input_key,
                placeholder="Type your answer here..." if not prev_input else "",
                label_visibility="collapsed"
            )
            
            # Streamlit widgets with keys automatically update st.session_state[key]
            # Get the current widget value
            widget_val = st.session_state.get(user_input_key, "")
            
            # Sync to user_inputs if changed
            if widget_val != st.session_state.user_inputs.get(occ_id, ""):
                st.session_state.user_inputs[occ_id] = widget_val
                
                # Validate input
                if widget_val:
                    valid, error = validate_input(label, widget_val, question)
                    if valid:
                        if occ_id in st.session_state.validation_errors:
                            del st.session_state.validation_errors[occ_id]
                        # Store in global responses so subsequent occurrences can use it
                        st.session_state.responses_global[label_upper] = widget_val
                        # Update other occurrences of the same label that don't have user input yet
                        for other_occ in occs:
                            other_occ_id = other_occ["id"]
                            other_label_upper = other_occ["label"].upper()
                            if other_label_upper == label_upper and other_occ_id != occ_id:
                                other_input_key = f"input_{other_occ_id}"
                                # Only update if the other field is empty and not manually set
                                if not st.session_state.get(other_input_key, "") and other_occ_id not in st.session_state.user_inputs:
                                    st.session_state[other_input_key] = widget_val
                                    st.session_state.user_inputs[other_occ_id] = widget_val
                    else:
                        st.session_state.validation_errors[occ_id] = error
                else:
                    # Clear error if input is empty
                    if occ_id in st.session_state.validation_errors:
                        del st.session_state.validation_errors[occ_id]
            
            # Show validation error if any
            if occ_id in st.session_state.validation_errors:
                st.error(st.session_state.validation_errors[occ_id])
    
    # Process button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Process All Answers", disabled=filled_count < total_count, type="primary", use_container_width=True):
            # Process all user inputs through LLM
            with st.spinner("🔄 Processing your answers..."):
                all_valid = True
                for occ in occs:
                    occ_id = occ["id"]
                    label = occ["label"].upper()
                    context = st.session_state.context_map.get(occ_id, "")
                    
                    # Skip if already auto-filled
                    if occ_id in st.session_state.responses_occurrence:
                        if st.session_state.responses_occurrence[occ_id]:
                            continue
                    
                    # Get input from widget or session state
                    input_widget_key = f"input_{occ_id}"
                    user_input = st.session_state.get(input_widget_key, st.session_state.user_inputs.get(occ_id, "")).strip()
                    if not user_input:
                        all_valid = False
                        continue
                    
                    # Update session state
                    st.session_state.user_inputs[occ_id] = user_input
                    
                    # Validate - get question from session state
                    question_text = st.session_state.placeholder_questions.get(occ_id, "")
                    valid, error = validate_input(label, user_input, question_text)
                    if not valid:
                        st.session_state.validation_errors[occ_id] = error
                        all_valid = False
                        continue
                    
                    # Process through LLM
                    prev_global = st.session_state.responses_global.get(label, "")
                    prev_occ = st.session_state.responses_occurrence.get(occ_id, "")
                    
                    try:
                        res = send_request_with_auth(
                            "chat_fill",
                            data={
                                "placeholder": label,
                                "context": context,
                                "user_input": user_input,
                                "previous_global_value": prev_global,
                                "prior_occurrence_value": prev_occ,
                            },
                            timeout=60,
                        )
                        
                        if res.ok:
                            ai = res.json()
                            action = ai.get("action", "ask")
                            filled = ai.get("filled_value", "").strip()
                            
                            if action == "fill" and filled:
                                st.session_state.responses_occurrence[occ_id] = filled
                                if label not in st.session_state.responses_global:
                                    st.session_state.responses_global[label] = filled
                            elif action == "reuse" and prev_global:
                                st.session_state.responses_occurrence[occ_id] = prev_global
                            else:
                                # Use user input as-is if LLM doesn't fill
                                st.session_state.responses_occurrence[occ_id] = user_input
                                if label not in st.session_state.responses_global:
                                    st.session_state.responses_global[label] = user_input
                    except Exception as e:
                        # Fallback to user input
                                st.session_state.responses_occurrence[occ_id] = user_input
                                if label not in st.session_state.responses_global:
                                    st.session_state.responses_global[label] = user_input
                
                if all_valid:
                    st.session_state.review_mode = True
                    st.rerun()
                else:
                    st.warning("⚠️ Please fix validation errors and try again.")

# ========== STEP 3: REVIEW & DOWNLOAD ==========
# Check if all are filled
all_filled = (
    st.session_state.get("extraction_complete", False) and
    st.session_state.get("occurrences") and
    st.session_state.get("questions_initialized", False) and
    all(
        st.session_state.responses_occurrence.get(occ["id"], "") 
        for occ in st.session_state.occurrences
    )
)

if all_filled or st.session_state.review_mode:
    st.markdown("---")
    st.markdown("### 📋 Step 3: Review & Download")
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.success("✅ All placeholders completed! Please review your entries below.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show ordered responses in a nice table format
    st.markdown("#### Your Entries")
    
    ordered_responses = [
        {
            "Placeholder": occ["label"],
            "Value": st.session_state.responses_occurrence.get(occ["id"], ""),
        }
        for occ in st.session_state.occurrences
    ]
    
    # Display as a nice dataframe
    df = pd.DataFrame(ordered_responses)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Generate and download section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📄 Generate & Download Document", type="primary", use_container_width=True):
            with st.spinner("🔄 Generating your completed document..."):
                files = {
                    "file": (
                        st.session_state.doc_name,
                        st.session_state.doc_bytes,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                }
                # Send ordered list of occurrences with their values to preserve order
                # This ensures each placeholder (even with same label) gets its unique value
                ordered_responses = [
                    {
                        "id": occ["id"],
                        "label": occ["label"],
                        "value": st.session_state.responses_occurrence.get(occ["id"], "")
                    }
                    for occ in st.session_state.occurrences
                ]
                data = {"responses": json.dumps(ordered_responses)}
                
                try:
                    res = requests.post(f"{BACKEND_URL}/fill_doc", files=files, data=data, timeout=120)
                    if res.ok:
                        st.success("✅ Document generated successfully!")
                        st.download_button(
                            label="⬇️ Download Completed Document",
                            data=res.content,
                            file_name=f"completed_{st.session_state.doc_name}",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Error generating document. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
