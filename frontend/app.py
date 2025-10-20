import streamlit as st
import requests
import json

# --- Streamlit Page Config ---
st.set_page_config(page_title="Lexsy Legal Assistant", page_icon="⚖️", layout="centered")

st.title("⚖️ Lexsy AI – Legal Document Parser")
st.write("Upload a `.docx` legal template to extract placeholders automatically.")

# --- Backend URL ---
BACKEND_URL = "http://127.0.0.1:8000" 

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
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        try:
            res = requests.post(f"{BACKEND_URL}/parse_doc", files=files, timeout=60)
            if res.ok:
                data = res.json()
                st.success("✅ Document parsed successfully!")
                st.subheader("📄 Text Preview")
                st.text_area("Preview", data["text_preview"], height=300)

                st.subheader("🔍 Detected Placeholders (in order)")
                occs = list(data.get("occurrences", [])) 

                if len(occs) > 0:
                    st.write([f"{o['id']}: {o['label']}" for o in occs])
                else:
                    st.info("No placeholders detected.")

                # Save to session
                st.session_state.occurrences = occs
                st.session_state.context_map = data.get("context_map", {})
                st.session_state.responses_global = {}
                st.session_state.responses_occurrence = {}
                st.session_state.current_index = 0
                st.session_state.conversation_started = True
                st.session_state.doc_bytes = uploaded_file.getvalue()
                st.session_state.doc_name = uploaded_file.name

            else:
                st.error(f"Backend error: {res.status_code}")
        except Exception as e:
            st.error(f"Request failed: {e}")

# === Conversational Placeholder Filling (LLM-powered) ===
if st.session_state.conversation_started and st.session_state.occurrences:
    st.header("💬 Lexsy AI – Interactive Document Assistant")

    occs = list(st.session_state.occurrences)  
    i = st.session_state.current_index

    if i < len(occs):
        occ = occs[i]
        occ_id = occ["id"]
        label = occ["label"].upper()
        context = st.session_state.context_map.get(occ_id, "")

        prev_global = st.session_state.responses_global.get(label, "")
        prev_occ = st.session_state.responses_occurrence.get(occ_id, "")

        # 1) Generate initial question or reuse decision
        if (
            "pending_question_for" not in st.session_state
            or st.session_state.get("pending_question_for") != occ_id
        ):
            with st.spinner("Thinking..."):
                init = requests.post(
                    f"{BACKEND_URL}/chat_fill",
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

                if action0 == "reuse" and prev_global:
                    st.chat_message("assistant").write(f"Reusing **{label}** → **{prev_global}**")
                    st.session_state.responses_occurrence[occ_id] = prev_global
                    st.session_state.current_index += 1
                    st.rerun()
                elif action0 == "fill" and filled0:
                    st.chat_message("assistant").write(f"**{label}** → **{filled0}**")
                    st.session_state.responses_occurrence[occ_id] = filled0
                    if label not in st.session_state.responses_global:
                        st.session_state.responses_global[label] = filled0
                    st.session_state.current_index += 1
                    st.rerun()
                else:
                    st.session_state["pending_question_for"] = occ_id
                    st.session_state["pending_question_text"] = (
                        q0 or f"Please provide the value for **{label}**."
                    )
                    st.rerun()
            else:
                st.error("⚠️ Error contacting /chat_fill.")
                st.stop()

        # 2) Ask or clarify
        if st.session_state.get("pending_question_for") == occ_id:
            st.chat_message("assistant").write(
                st.session_state.get(
                    "pending_question_text", f"Please provide **{label}**."
                )
            )

            user_input = st.chat_input("Type your response…")
            if user_input:
                with st.spinner("Checking…"):
                    res = requests.post(
                        f"{BACKEND_URL}/chat_fill",
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
                    followup = ai.get("followup_question", "").strip()

                    if action == "reuse" and prev_global:
                        st.chat_message("assistant").write(f"Reusing **{label}** → **{prev_global}**")
                        st.session_state.responses_occurrence[occ_id] = prev_global
                        st.session_state.current_index += 1
                        st.session_state.pop("pending_question_for", None)
                        st.session_state.pop("pending_question_text", None)
                        st.rerun()
                    elif action == "fill" and filled:
                        st.chat_message("assistant").write(f"Got it. **{label}** → **{filled}**")
                        st.session_state.responses_occurrence[occ_id] = filled
                        if label not in st.session_state.responses_global:
                            st.session_state.responses_global[label] = filled
                        st.session_state.current_index += 1
                        st.session_state.pop("pending_question_for", None)
                        st.session_state.pop("pending_question_text", None)
                        st.rerun()
                    else:
                        st.session_state["pending_question_text"] = (
                            followup or f"Please clarify the value for **{label}**."
                        )
                        st.rerun()

    else:
        # --- Completed all placeholders ---
        st.success("✅ All placeholders completed!")
        st.subheader("Your entries")

        # Show ordered responses in exact doc order
        ordered_responses = [
            {
                "id": occ["id"],
                "label": occ["label"],
                "value": st.session_state.responses_occurrence.get(occ["id"], ""),
            }
            for occ in st.session_state.occurrences
        ]
        st.json(ordered_responses)

        # --- Generate completed document ---
        if st.button("📄 Generate Completed Document"):
            with st.spinner("Generating document..."):
                files = {
                    "file": (
                        st.session_state.doc_name,
                        st.session_state.doc_bytes,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                }
                # Maintain ordered placeholder→value mapping
                filled_map = {
                    occ["label"]: st.session_state.responses_occurrence.get(occ["id"], "")
                    for occ in st.session_state.occurrences
                }
                data = {"responses": json.dumps(filled_map)}

                res = requests.post(f"{BACKEND_URL}/fill_doc", files=files, data=data)
                if res.ok:
                    st.download_button(
                        label="⬇️ Download Filled Document",
                        data=res.content,
                        file_name="completed_document.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    st.error("❌ Error generating document.")
