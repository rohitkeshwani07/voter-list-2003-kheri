import PyPDF2

# Test with the first PDF
pdf_file = "eci_pdfs/S24_54_1.pdf"

with open(pdf_file, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    print(f"Number of pages: {len(pdf_reader.pages)}")
    print("\n" + "="*80)
    print("First page content:")
    print("="*80)

    # Extract text from first page
    page = pdf_reader.pages[0]
    text = page.extract_text()
    print(text)

    if len(pdf_reader.pages) > 1:
        print("\n" + "="*80)
        print("Second page content:")
        print("="*80)
        page = pdf_reader.pages[1]
        text = page.extract_text()
        print(text)
