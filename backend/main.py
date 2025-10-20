from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils.parser import extract_placeholders
from fastapi.responses import FileResponse
from utils.filler import fill_placeholders
import json
from ast import literal_eval
from utils.conversation import handle_conversational_turn

import tempfile

app = FastAPI(title="Lexsy AI Backend")

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "lexsy-backend"}

@app.post("/parse_doc")
async def parse_doc(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result = extract_placeholders(tmp_path)
    return result


@app.post("/fill_doc")
async def fill_doc(
    file: UploadFile = File(...),
    responses: str = Form(...)
):
    print("📨 Received /fill_doc request")

    try:
        if not responses:
            raise ValueError("No responses data received")

        # Parse responses JSON safely
        try:
            data = json.loads(responses)
            print("✅ Parsed JSON successfully")
        except Exception:
            data = literal_eval(responses)
            print("⚙️ Used literal_eval fallback")

        # Read file content
        content = await file.read()
        print(f"📁 File received: {file.filename}, size = {len(content)} bytes")

        # Generate filled document
        output_path = fill_placeholders(content, data)
        print(f"✅ Filled document generated: {output_path}")

        return FileResponse(
            output_path,
            filename="completed_document.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print("❌ Error in /fill_doc:", e)
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/chat_fill")
async def chat_fill(
    placeholder: str = Form(...),
    context: str = Form(...),
    user_input: str = Form(""),
    previous_global_value: str | None = Form(None),
    prior_occurrence_value: str | None = Form(None),
):
    """
    LLM-powered conversational endpoint:
    Returns action: reuse | fill | ask, plus filled_value/followup_question.
    """
    try:
        result = handle_conversational_turn(
            placeholder_label=placeholder,
            occurrence_context=context,
            user_input=user_input,
            previous_global_value=previous_global_value,
            prior_occurrence_value=prior_occurrence_value
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))