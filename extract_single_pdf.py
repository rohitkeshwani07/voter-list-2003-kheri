#!/usr/bin/env python3
"""
Extract names from a single PDF with filename included in output
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

# Process first PDF as test
pdf_file = Path('eci_pdfs/S24_54_1.pdf')
temp_dir = Path('temp_ocr')
temp_dir.mkdir(exist_ok=True)

print(f"Processing single PDF: {pdf_file.name}", flush=True)

names = process_pdf(pdf_file, temp_dir)

# Save with filename prefix
output_file = 'single_pdf_output.txt'
print(f"\nSaving {len(names)} names to {output_file}...", flush=True)

with open(output_file, 'w', encoding='utf-8') as f:
    for name in names:
        f.write(f"{pdf_file.name}\t{name}\n")

print(f"\nDone! Output format:")
print(f"FILENAME<TAB>NAME")
print(f"\nFirst 20 entries:")
with open(output_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if i > 20:
            break
        print(line.rstrip())

# Clean up temp directory
import shutil
if temp_dir.exists():
    shutil.rmtree(temp_dir)

print(f"\nTotal entries: {len(names)}")
print(f"Output saved to: {output_file}")
