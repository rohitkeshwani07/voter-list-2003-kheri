#!/usr/bin/env python3
"""
Test extraction on first 3 PDFs
"""
import subprocess
import os
import re
from pathlib import Path
import sys

def convert_pdf_to_images(pdf_path, output_dir):
    """Convert PDF pages to PNG images"""
    print(f"Converting {pdf_path}...", flush=True)
    cmd = [
        'pdftoppm',
        pdf_path,
        f'{output_dir}/page',
        '-png'
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

def extract_names_from_text(text):
    """Extract names from OCR text"""
    names = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = re.split(r'\s{2,}|\t|\|', line)

        for part in parts:
            part = part.strip()
            if re.search(r'[\u0900-\u097F]', part):
                cleaned = re.sub(r'[0-9\(\)\[\]\/\\]', ' ', part)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()

                if len(cleaned) >= 2 and re.search(r'[\u0900-\u097F]', cleaned):
                    names.append(cleaned)

    return names

def process_pdf(pdf_path, temp_dir):
    """Process a single PDF and extract all names"""
    print(f"\nProcessing: {pdf_path}", flush=True)

    images = convert_pdf_to_images(pdf_path, temp_dir)
    if not images:
        print(f"No images generated for {pdf_path}", flush=True)
        return []

    all_names = []

    for i, image in enumerate(images, 1):
        print(f"  OCR page {i}/{len(images)}...", flush=True)
        text = ocr_image(image)
        names = extract_names_from_text(text)
        all_names.extend(names)

    print(f"  Extracted {len(all_names)} name entries from {len(images)} pages", flush=True)

    for image in images:
        image.unlink()

    return all_names

# Test with first 3 PDFs
pdf_dir = Path('eci_pdfs')
temp_dir = Path('temp_ocr')
temp_dir.mkdir(exist_ok=True)

pdf_files = sorted(pdf_dir.glob('*.pdf'))[:3]  # Only first 3
print(f"Testing with {len(pdf_files)} PDF files", flush=True)

all_names = []

for i, pdf_file in enumerate(pdf_files, 1):
    print(f"\n{'='*60}", flush=True)
    print(f"PDF {i}/{len(pdf_files)}: {pdf_file.name}", flush=True)
    print(f"{'='*60}", flush=True)

    try:
        names = process_pdf(pdf_file, temp_dir)
        all_names.extend(names)
    except Exception as e:
        print(f"Error processing {pdf_file}: {e}", flush=True)
        continue

print(f"\n{'='*60}", flush=True)
print(f"Test complete! Total names extracted: {len(all_names)}", flush=True)
print(f"Saving to test_names.txt...", flush=True)
print(f"{'='*60}", flush=True)

with open('test_names.txt', 'w', encoding='utf-8') as f:
    for name in all_names:
        f.write(name + '\n')

print(f"\nDone! Names saved to test_names.txt", flush=True)
print(f"First 10 names:", flush=True)
for name in all_names[:10]:
    print(f"  {name}", flush=True)
