# ⚖️ Lexsy AI – Legal Document Assistant

## 🧩 Overview

Lexsy AI is an **intelligent legal document assistant** that allows users to upload legal templates (e.g., `.docx` SAFE agreements) and automatically fill in placeholders through a **conversational AI experience**.

Using an LLM (OpenAI GPT-4o-mini), the app:

* Detects placeholders like `[Company Name]`, `$[__________]`, `<Investor Name>`, etc.
* Extracts local **context** from surrounding text.
* Asks context-aware, natural questions to fill in the missing details.
* Avoids repetitive questions for identical fields (like company name).
* Generates a completed, downloadable `.docx` file.

This project demonstrates **LLM-driven document completion** with a modular backend and interactive frontend.

---

## 🏗️ Project Structure

```text
lexsy-ai-law-firm/
│
├── backend/
│   ├── main.py               # FastAPI backend entry point
│   ├── utils/
│   │   ├── parser.py         # Extracts placeholders + contextual snippets
│   │   ├── filler.py         # Replaces placeholders in docx
│   │   ├── conversation.py   # Handles LLM-based conversational turns
│
├── frontend/
│   ├── app.py                # Streamlit conversational frontend
│
└── README.md
```

---

## ⚙️ Features

* ✅ Upload `.docx` templates
* ✅ Automatically detect placeholders (e.g., `[Company Name]`, `$[_____]`)
* ✅ Extract contextual text around placeholders
* ✅ Generate context-aware questions using GPT
* ✅ Avoid redundant questions for repeating fields
* ✅ Real-time chat-based document filling
* ✅ Download the completed document

---

## 🚀 Setup & Usage

### 1️⃣ Prerequisites

* Python 3.9+
* [OpenAI API key](https://platform.openai.com)
* pip / virtualenv
* Streamlit

---

### 2️⃣ Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/lexsy-ai-law-firm.git
cd lexsy-ai-law-firm

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

### 3️⃣ Environment Variable

Set your OpenAI API key permanently:

**Windows PowerShell**

```bash
setx OPENAI_API_KEY "sk-xxxxxx"
```

**macOS/Linux**

```bash
export OPENAI_API_KEY="sk-xxxxxx"
```

---

### 4️⃣ Run the Backend

From the `backend` folder:

```bash
uvicorn main:app --reload
```

Backend starts at 👉 `http://127.0.0.1:8000`

---

### 5️⃣ Run the Frontend

In a new terminal:

```bash
cd frontend
streamlit run app.py
```

Frontend runs at 👉 `http://localhost:8501`

---

## 🧠 Example Flow

1. Upload your legal `.docx` template (e.g., SAFE agreement).

2. The backend extracts placeholders and their contexts.

3. The AI assistant asks context-aware questions like:

   > “What is the name of the investor?”
   > “What is the post-money valuation cap (in USD)?”

4. You respond conversationally.

5. Once all placeholders are filled, download the completed `.docx` file.

---

## 🧩 Tech Stack

| Component        | Technology                   |
| ---------------- | ---------------------------- |
| Backend          | FastAPI                      |
| Frontend         | Streamlit                    |
| AI Model         | GPT-4o-mini (via OpenAI API) |
| Document Parsing | python-docx                  |
| Environment      | Python 3.10+                 |

---

## 🧪 Example Output

![Lexsy Demo Screenshot](assets/demo.png) - will post soon

---

## 🧱 Future Improvements

* Context-aware refinement for monetary fields (detect “Purchase Amount”, “Valuation Cap”, etc.)
* Multi-user session persistence
* Editable previews before document generation
* Support for PDFs and scanned documents (via OCR)
* Integration with legal template APIs

---

