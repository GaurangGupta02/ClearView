import pdfplumber

def extract_text_from_pdf(pdf_path):
    text_pages = [] 
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    print(f"Warning: No text extracted from page {page.page_number}")
                text_pages.append(text if text else "")
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return []
    
    return text_pages

