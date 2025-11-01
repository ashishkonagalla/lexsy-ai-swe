# utils/conversation.py
from openai import OpenAI
import json
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a legal document assistant filling placeholders in uploaded contracts.

INPUT YOU RECEIVE:
- placeholder_label: the normalized label of this occurrence (e.g., "COMPANY NAME", "$[__________]", "DATE OF SAFE").
- occurrence_context: ~80 words around this occurrence from the document.
- previous_global_value: value already provided for the same label elsewhere (or empty).
- prior_occurrence_value: value already provided for this exact occurrence (or empty).
- user_input: the user's latest response (may be empty on the first turn).

YOUR JOB:
Decide one of:
- "reuse": reuse previous_global_value for this occurrence (same entity across doc).
- "fill": extract/normalize a new value from user_input for this occurrence.
- "ask": ask a short, specific question that includes the context so the user knows exactly what is needed.

GUIDANCE:
- Identity-like labels (company name, investor name, date of safe, state of incorporation) often REUSE.
- Money-like fields (contains '$', 'purchase amount/price', 'valuation cap') are often UNIQUE per occurrence → ASK each time (or FILL if user provided).
- If user_input clearly provides the value, choose "fill".
- When you ASK, include the concrete thing from context (e.g., “purchase amount for this SAFE”, “valuation cap”, “subscription price”).
- Never fabricate values.

OUTPUT STRICT JSON ONLY, e.g.:
{
  "action": "ask",
  "filled_value": "",
  "followup_question": "What is the purchase amount for this SAFE?",
  "confidence": 0.85
}
"""

def handle_conversational_turn(
    placeholder_label: str,
    occurrence_context: str,
    user_input: str = "",
    previous_global_value: str | None = None,
    prior_occurrence_value: str | None = None,
    api_key: str | None = None,
):

    client = OpenAI(api_key=api_key)

    payload = {
        "placeholder_label": placeholder_label,
        "occurrence_context": occurrence_context,
        "previous_global_value": previous_global_value or "",
        "prior_occurrence_value": prior_occurrence_value or "",
        "user_input": user_input or "",
    }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": json.dumps(payload)}
            ],
        )
        raw = resp.choices[0].message.content.strip()
        # Try to parse strict JSON; fall back to asking if malformed
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "action": "ask",
                "filled_value": "",
                "followup_question": raw,
                "confidence": 0.4
            }

        # Normalize keys
        data.setdefault("action", "ask")
        data.setdefault("filled_value", "")
        data.setdefault("followup_question", "")
        data.setdefault("confidence", 0.6)
        return data

    except Exception as e:
        return {
            "action": "ask",
            "filled_value": "",
            "followup_question": f"Sorry, I hit an error. Please provide this value: {placeholder_label}",
            "confidence": 0.0
        }
