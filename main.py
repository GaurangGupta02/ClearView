from modules.extractor import extract_text_from_pdf
from modules.replacer import load_abbreviations, replace_with_abbreviations
from modules.abbreviator import abbreviate_pdf 

pdf_path = "Sample.pdf" 
output_path = "minimized_output.pdf"

text_pages = extract_text_from_pdf(pdf_path)

abbreviations = load_abbreviations("config/abbreviations.json")
replaced_pages = replace_with_abbreviations(text_pages, abbreviations)

abbreviate_pdf(pdf_path, output_path, abbreviations, show_reference=False)
