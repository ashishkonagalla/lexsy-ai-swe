from docx import Document
import tempfile
import re

def fill_placeholders(file_bytes: bytes, responses: dict):
    print("\n==============================")
    print("🧾 Starting fill_placeholders()")
    print("Responses received:", responses)
    print("==============================\n")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
        print(f"📁 Temporary file created at: {tmp_path}")

    doc = Document(tmp_path)
    print("✅ Document loaded successfully.")

    def replace_in_paragraph(paragraph):
        """Replace placeholders including [KEY], {{KEY}}, $[____], and underline blanks."""
        full_text = "".join(run.text for run in paragraph.runs)
        replaced_text = full_text

        # --- 1️⃣ Normal bracketed placeholders ---
        for key, value in responses.items():
            if key not in ("$[__________]", "_____________"):
                patterns = [
                    rf"\[\s*{re.escape(key)}\s*\]",   # [KEY]
                    rf"\{{\s*{re.escape(key)}\s*\}}", # {KEY}
                ]
                for pattern in patterns:
                    if re.search(pattern, replaced_text, flags=re.IGNORECASE):
                        replaced_text = re.sub(pattern, str(value), replaced_text, flags=re.IGNORECASE)
                        print(f"🔁 Replacing placeholder '{key}' with '{value}'")

        # --- 2️⃣ Money placeholders: $[__________] ---
        money_value = responses.get("$[__________]")
        if money_value:
            if re.search(r"\$\s*\[[^\]]+\]", replaced_text):
                replaced_text = re.sub(
                    r"\$\s*\[[^\]]+\]",
                    f"${money_value}",
                    replaced_text
                )
                print(f"💰 Replacing money placeholder with '${money_value}'")

        # --- 3️⃣ Underline blanks: ___________ ---
        underline_value = responses.get("_____________")
        if underline_value:
            if re.search(r"_{3,}", replaced_text):
                replaced_text = re.sub(r"_{3,}", str(underline_value), replaced_text)
                print(f"🖊️ Replacing underline blanks with '{underline_value}'")

        # --- 4️⃣ Write back to paragraph runs ---
        if full_text != replaced_text:
            for run in paragraph.runs:
                run.text = ""
            if paragraph.runs:
                paragraph.runs[0].text = replaced_text
            else:
                paragraph.add_run(replaced_text)

    def process_element(element):
        """Recursively process all paragraphs and tables."""
        if hasattr(element, "paragraphs"):
            for p in element.paragraphs:
                replace_in_paragraph(p)
        if hasattr(element, "tables"):
            for t in element.tables:
                for r in t.rows:
                    for c in r.cells:
                        process_element(c)

    # Process all paragraphs and tables in the main body
    process_element(doc)

    # Process headers and footers
    for section in doc.sections:
        if section.header:
            process_element(section.header)
        if section.footer:
            process_element(section.footer)

    # Save filled file
    output_path = tmp_path.replace(".docx", "_filled.docx")
    doc.save(output_path)
    print(f"✅ Document saved successfully at: {output_path}")
    print("==============================\n")

    return output_path
