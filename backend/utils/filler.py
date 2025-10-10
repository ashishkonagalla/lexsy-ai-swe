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
        """Replace only bracketed placeholders, ignoring normal words."""
        full_text = "".join(run.text for run in paragraph.runs)
        replaced_text = full_text

        # Replace only [PLACEHOLDER] or {{PLACEHOLDER}} patterns
        for key, value in responses.items():
            patterns = [
                rf"\[\s*{re.escape(key)}\s*\]",  # [Company Name]
                rf"\{{\s*{re.escape(key)}\s*\}}",  # {Company Name}
            ]
            for pattern in patterns:
                if re.search(pattern, replaced_text, flags=re.IGNORECASE):
                    replaced_text = re.sub(pattern, value, replaced_text, flags=re.IGNORECASE)
                    print(f"🔁 Replacing placeholder '{key}' with '{value}'")

        if full_text != replaced_text:
            for run in paragraph.runs:
                run.text = ""
            paragraph.runs[0].text = replaced_text

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
