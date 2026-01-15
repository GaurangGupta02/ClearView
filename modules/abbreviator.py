import fitz  # PyMuPDF 
import re

def abbreviate_pdf(input_path, output_path, abbreviations, return_used=False, include_reference_pages=False):
    original_doc = fitz.open(input_path)
    new_doc = fitz.open()
    used_abbr = {}
    replacement_details = {}

    for page in original_doc:
        # Extract plain text (no layout)
        text = page.get_text()

        # Abbreviate terms
        for full, abbr in abbreviations.items():
            pattern = r'\b' + re.escape(full) + r'\b'
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
            if matches:
                text = re.sub(pattern, abbr, text, flags=re.IGNORECASE)
                used_abbr[full] = abbr
                replacement_details[full] = {
                    "abbr": abbr,
                    "count": replacement_details.get(full, {}).get("count", 0) + len(matches)
                }

        # Add abbreviated text to new page
        new_page = new_doc.new_page(width=595, height=842)
        new_page.insert_textbox(
            fitz.Rect(40, 50, 555, 800),
            text,
            fontsize=11,
            fontname="helv",
            color=(0, 0, 0),
        )

    # Add reference page if toggle is ON and there are abbreviations
    if include_reference_pages and used_abbr:
        ref_page = new_doc.new_page(width=595, height=842)
        y = 50
        ref_page.insert_text((40, y), "Abbreviation Reference Table", fontsize=14, fontname="helv")
        y += 30

        for full, data in sorted(replacement_details.items()):
            line = f"{full} ➝ {data['abbr']} (Replaced {data['count']} times)"
            if y > 800:
                # Add new page if current page is full
                ref_page = new_doc.new_page(width=595, height=842)
                y = 50
            ref_page.insert_text((40, y), line, fontsize=11, fontname="helv")
            y += 20

    new_doc.save(output_path)
    print(f"Minimized PDF saved to {output_path}")

    if return_used:
        return replacement_details
