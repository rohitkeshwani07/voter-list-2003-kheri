#!/usr/bin/env python3
"""
Extract names from PDF with improved filtering (inspired by user's code)
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
    print(f"Converting PDF to images (starting from page {start_page})...", flush=True)
    cmd = [
        'pdftoppm',
        pdf_path,
        f'{output_dir}/page',
        '-png',
        '-f', str(start_page)  # Start from page 2 (skip cover)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if result.returncode != 0:
        print(f"Error converting {pdf_path}", flush=True)
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

def extract_names_from_pdf(pdf_path, temp_dir, verbose=True):
    """Process a PDF and extract valid names only"""
    if verbose:
        print(f"\nProcessing: {pdf_path}", flush=True)

    # Convert PDF to images (skip first page)
    images = convert_pdf_to_images(pdf_path, temp_dir, start_page=2)
    if not images:
        print(f"No images generated for {pdf_path}", flush=True)
        return []

    all_names = []

    if verbose:
        print(f"Processing {len(images)} pages with OCR...", flush=True)

    for i, image in enumerate(images, 2):  # Start from page 2
        if verbose:
            print(f"  Page {i}...", end=' ', flush=True)

        text = ocr_image(image)
        lines = text.split('\n')

        page_names = 0
        for line in lines:
            line = line.strip()
            if is_valid_name(line):
                all_names.append(line)
                page_names += 1

        if verbose:
            print(f"✓ Found {page_names} names", flush=True)

    if verbose:
        print(f"  Total: {len(all_names)} names extracted", flush=True)

    # Clean up images
    for image in images:
        image.unlink()

    return all_names

# Process single PDF as test
pdf_file = Path('eci_pdfs/S24_54_1.pdf')
temp_dir = Path('temp_ocr')
temp_dir.mkdir(exist_ok=True)

print("="*60)
print(f"Testing improved extraction on: {pdf_file.name}")
print("="*60)

names = extract_names_from_pdf(pdf_file, temp_dir, verbose=True)

print("="*60)
print(f"\n✓ Extraction complete!")
print(f"Total names found: {len(names)}")

# Display first 20 names
if names:
    print(f"\nFirst {min(20, len(names))} names:")
    for idx, name in enumerate(names[:20], 1):
        print(f"  {idx}. {name}")

# Save to CSV with filename
csv_file = 'test_output.csv'
print(f"\n✓ Saving to CSV: {csv_file}")

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF_File', 'Serial', 'Name'])
    for idx, name in enumerate(names, 1):
        writer.writerow([pdf_file.name, idx, name])

print(f"✓ Done! {len(names)} names saved to {csv_file}")

# Show sample CSV output
print(f"\nSample CSV format:")
with open(csv_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 10:
            break
        print(f"  {line.rstrip()}")

# Clean up temp directory
import shutil
if temp_dir.exists():
    shutil.rmtree(temp_dir)
