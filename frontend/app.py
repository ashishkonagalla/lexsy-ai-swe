import streamlit as st
import requests
import json

# --- Streamlit Page Config ---
st.set_page_config(page_title="Lexsy Legal Assistant", page_icon="⚖️", layout="centered")

st.title("⚖️ Lexsy AI – Legal Document Parser")
st.write("Upload a `.docx` legal template to extract placeholders automatically.")

# --- Backend URL ---
BACKEND_URL = "http://127.0.0.1:8000"  # change this later when deployed

# --- Initialize session state ---
st.session_state.setdefault("placeholders", [])
st.session_state.setdefault("responses", {})
st.session_state.setdefault("current_index", 0)
st.session_state.setdefault("conversation_started", False)
st.session_state.setdefault("doc_bytes", None)
st.session_state.setdefault("doc_name", None)

# --- File Upload Section ---
uploaded_file = st.file_uploader("Upload your legal document (.docx)", type=["docx"])

if uploaded_file and st.button("Extract Placeholders"):
    with st.spinner("Processing document..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(),
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        try:
            res = requests.post(f"{BACKEND_URL}/parse_doc", files=files, timeout=60)
            if res.ok:
                data = res.json()
                st.success("✅ Document parsed successfully!")
                st.subheader("📄 Text Preview")
                st.text_area("Preview", data["text_preview"], height=300)

                st.subheader("🔍 Detected Placeholders")
                if data["placeholders"]:
                    st.write(data["placeholders"])
                else:
                    st.info("No placeholders detected.")

                # Save placeholders & file for later runs
                clean = [p for p in data["placeholders"] if p and p.strip()]  # drop empty or ****
                st.session_state.placeholders = clean
                st.session_state.responses = {}
                st.session_state.current_index = 0
                st.session_state.conversation_started = True
                st.session_state.doc_bytes = uploaded_file.getvalue()
                st.session_state.doc_name = uploaded_file.name

            else:
                st.error(f"Backend error: {res.status_code}")
        except Exception as e:
            st.error(f"Request failed: {e}")

# === Conversational Placeholder Filling (top-level) ===
if st.session_state.conversation_started and st.session_state.placeholders:
    st.header("💬 Fill in Document Details")

    placeholders = st.session_state.placeholders
    index = st.session_state.current_index

    if index < len(placeholders):
        current_placeholder = placeholders[index]
        st.chat_message("assistant").write(f"Please provide a value for **{current_placeholder}**:")

        user_input = st.chat_input("Type your answer here...")
        if user_input:
            st.session_state.responses[current_placeholder] = user_input.strip()
            st.session_state.current_index += 1
            st.rerun()

    else:
        st.success("✅ All placeholders filled!")
        st.write("Here’s what you entered:")
        st.json(st.session_state.responses)
        # (Next step) Add "Generate Completed Document" button here

        if st.button("📄 Generate Completed Document"):
            with st.spinner("Generating filled document..."):
                files = {
                    "file": (st.session_state.doc_name, st.session_state.doc_bytes,
                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                }
                data = {"responses": json.dumps(st.session_state.responses)}
                res = requests.post(f"{BACKEND_URL}/fill_doc", files=files, data=data)
                if res.ok:
                    st.download_button(
                        label="⬇️ Download Filled Document",
                        data=res.content,
                        file_name="completed_document.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.error("Error generating document")