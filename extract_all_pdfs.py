#!/usr/bin/env python3
"""
Extract names from ALL 281 ECI PDFs with improved filtering and CSV output
"""
import subprocess
import csv
import re
from pathlib import Path
import sys

def is_valid_name(text):
    """Check if text is a valid name (not a header or label)"""
    if not text or len(text.strip()) < 3:
        return False

    text = text.strip()

    # Skip common headers and labels
    skip_words = [
        'निर्वाचक', 'मतदान', 'भाग', 'पुनरीक्षण', 'क्रमांक', 'नाम', 'लिंग',
        'आयु', 'मकान', 'पिता', 'माता', 'पति', 'पत्नी', 'संख्या', 'केंद्र',
        'पहचान', 'पत्र', 'फोटो', 'मुख्य', 'सहायक', 'विधान', 'सभा', 'क्षेत्र',
        'लोक', 'आरक्षण', 'स्थिति', 'पात्रता', 'तिथि', 'विवरण', 'ग्राम',
        'शहर', 'तहसील', 'जिला', 'सर्किल', 'स्थल', 'भवन', 'वर्गीकरण',
        'ग्रामीण', 'प्रकार', 'कुल', 'पुरुष', 'महिला', 'हैसियत', 'सामान्य'
    ]

    text_lower = text.lower()
    for skip in skip_words:
        if skip in text_lower:
            return False

    # Skip if mostly numbers or has many special characters
    if re.search(r'^\d+$', text):
        return False

    if re.search(r'[=\-\+\*\@\#\$\%\^\&]', text):
        return False

    # Check for Devanagari characters
    devanagari_count = sum(1 for char in text if '\u0900' <= char <= '\u097F')

    # Must have at least 3 Devanagari characters and reasonable length
    if devanagari_count >= 3 and 3 <= len(text) <= 50:
        return True

    return False

def convert_pdf_to_images(pdf_path, output_dir, start_page=2):
    """Convert PDF pages to PNG images, skipping first page"""
    cmd = [
        'pdftoppm',
        pdf_path,
        f'{output_dir}/page',
        '-png',
        '-f', str(start_page)  # Start from page 2 (skip cover)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if result.returncode != 0:
        return []

    images = sorted(Path(output_dir).glob('page-*.png'))
    return images

def ocr_image(image_path):
    """Run OCR on an image with Hindi+English support"""
    cmd = [
        'tesseract',
        str(image_path),
        'stdout',
        '-l', 'hin+eng'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout

def extract_names_from_pdf(pdf_path, temp_dir):
    """Process a PDF and extract valid names only"""
    # Convert PDF to images (skip first page)
    images = convert_pdf_to_images(pdf_path, temp_dir, start_page=2)
    if not images:
        return []

    all_names = []

    for image in images:
        text = ocr_image(image)
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if is_valid_name(line):
                all_names.append(line)

    # Clean up images
    for image in images:
        image.unlink()

    return all_names

def main():
    pdf_dir = Path('eci_pdfs')
    temp_dir = Path('temp_ocr')
    temp_dir.mkdir(exist_ok=True)

    output_file = 'all_names_final.csv'

    # Get all PDFs
    pdf_files = sorted(pdf_dir.glob('*.pdf'))
    total_pdfs = len(pdf_files)

    print("="*70, flush=True)
    print(f"ECI PDF Name Extraction - Processing {total_pdfs} PDFs", flush=True)
    print("="*70, flush=True)

    # Open CSV file for writing
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['PDF_File', 'Serial', 'Name'])

        total_names = 0

        # Process each PDF
        for pdf_idx, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{pdf_idx}/{total_pdfs}] Processing: {pdf_file.name}", flush=True)

            try:
                names = extract_names_from_pdf(pdf_file, temp_dir)

                # Write names to CSV
                for name_idx, name in enumerate(names, 1):
                    writer.writerow([pdf_file.name, name_idx, name])
                    total_names += 1

                print(f"  ✓ Extracted {len(names)} names (Total so far: {total_names})", flush=True)

                # Save progress periodically (every 10 PDFs)
                if pdf_idx % 10 == 0:
                    csvfile.flush()
                    print(f"\n--- Progress saved: {total_names} names from {pdf_idx} PDFs ---", flush=True)

            except Exception as e:
                print(f"  ✗ Error: {e}", flush=True)
                continue

    print("\n" + "="*70, flush=True)
    print(f"✓ EXTRACTION COMPLETE!", flush=True)
    print(f"  Total PDFs processed: {total_pdfs}", flush=True)
    print(f"  Total names extracted: {total_names}", flush=True)
    print(f"  Output file: {output_file}", flush=True)
    print("="*70, flush=True)

    # Clean up temp directory
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    main()
