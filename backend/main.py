from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from utils.parser import extract_placeholders
from utils.filler import fill_placeholders
from utils.conversation import handle_conversational_turn
import json, os, tempfile
from ast import literal_eval

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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    return extract_placeholders(tmp_path)


@app.post("/fill_doc")
async def fill_doc(file: UploadFile = File(...), responses: str = Form(...)):
    print("📨 Received /fill_doc request")
    try:
        if not responses:
            raise ValueError("No responses data received")
        try:
            data = json.loads(responses)
        except Exception:
            data = literal_eval(responses)
        content = await file.read()
        output_path = fill_placeholders(content, data)
        return FileResponse(
            output_path,
            filename="completed_document.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
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
    authorization: str | None = Header(None),
):
    """
    LLM-powered conversational endpoint.
    Supports either user-provided API key (via Authorization header)
    or falls back to the server default key.
    """
    try:
        # Extract user API key from Authorization: Bearer <key>
        user_key = None
        if authorization and authorization.startswith("Bearer "):
            user_key = authorization.split(" ")[1].strip()

        # Validate API key source
        api_key = user_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="❌ No OpenAI API key provided.")

        # Call conversation handler with explicit key
        result = handle_conversational_turn(
            placeholder_label=placeholder,
            occurrence_context=context,
            user_input=user_input,
            previous_global_value=previous_global_value,
            prior_occurrence_value=prior_occurrence_value,
            api_key=api_key,   # ✅ pass directly (avoid setting os.environ)
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))