#!/usr/bin/env python3
"""
Parallel PDF extraction with resume capability
Processes multiple PDFs simultaneously for faster extraction
"""
import subprocess
import csv
import re
from pathlib import Path
import sys
from multiprocessing import Pool, cpu_count
import time

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

    if re.search(r'^\d+$', text):
        return False

    if re.search(r'[=\-\+\*\@\#\$\%\^\&]', text):
        return False

    devanagari_count = sum(1 for char in text if '\u0900' <= char <= '\u097F')

    if devanagari_count >= 3 and 3 <= len(text) <= 50:
        return True

    return False

def convert_pdf_to_images(pdf_path, output_dir, start_page=2):
    """Convert PDF pages to PNG images, skipping first page"""
    cmd = [
        'pdftoppm',
        str(pdf_path),
        f'{output_dir}/page',
        '-png',
        '-f', str(start_page)
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

def process_single_pdf(pdf_path):
    """Process a single PDF and return (pdf_name, names_list)"""
    try:
        # Create unique temp directory for this PDF
        temp_dir = Path(f'temp_ocr_{pdf_path.stem}')
        temp_dir.mkdir(exist_ok=True)

        # Convert PDF to images (skip first page)
        images = convert_pdf_to_images(pdf_path, temp_dir, start_page=2)
        if not images:
            return (pdf_path.name, [])

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
            try:
                image.unlink()
            except:
                pass

        # Remove temp directory
        try:
            temp_dir.rmdir()
        except:
            pass

        return (pdf_path.name, all_names)

    except Exception as e:
        print(f"Error processing {pdf_path.name}: {e}", flush=True)
        return (pdf_path.name, [])

def get_processed_pdfs(csv_file):
    """Get set of already processed PDF filenames"""
    if not Path(csv_file).exists():
        return set()

    processed = set()
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row:
                    processed.add(row[0])
    except:
        pass

    return processed

def main():
    pdf_dir = Path('eci_pdfs')
    output_file = 'all_names_final.csv'

    # Get all PDFs
    all_pdf_files = sorted(pdf_dir.glob('*.pdf'))
    total_pdfs = len(all_pdf_files)

    # Check which PDFs are already processed
    processed_pdfs = get_processed_pdfs(output_file)

    # Filter to only unprocessed PDFs
    pdf_files = [pdf for pdf in all_pdf_files if pdf.name not in processed_pdfs]

    print("="*70, flush=True)
    print(f"Parallel PDF Name Extraction", flush=True)
    print(f"Total PDFs: {total_pdfs}", flush=True)
    print(f"Already processed: {len(processed_pdfs)}", flush=True)
    print(f"Remaining: {len(pdf_files)}", flush=True)
    print(f"Using {min(4, cpu_count())} parallel workers", flush=True)
    print("="*70, flush=True)

    if not pdf_files:
        print("\n✓ All PDFs already processed!", flush=True)
        return

    # Open CSV file for appending
    file_mode = 'a' if processed_pdfs else 'w'
    with open(output_file, file_mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header only if new file
        if not processed_pdfs:
            writer.writerow(['PDF_File', 'Serial', 'Name'])

        # Process PDFs in parallel (4 at a time)
        with Pool(processes=min(4, cpu_count())) as pool:
            completed = len(processed_pdfs)

            for pdf_name, names in pool.imap_unordered(process_single_pdf, pdf_files):
                completed += 1

                # Write names to CSV
                for idx, name in enumerate(names, 1):
                    writer.writerow([pdf_name, idx, name])

                csvfile.flush()  # Ensure data is written

                print(f"[{completed}/{total_pdfs}] ✓ {pdf_name}: {len(names)} names", flush=True)

    print("\n" + "="*70, flush=True)
    print(f"✓ EXTRACTION COMPLETE!", flush=True)
    print(f"  Output file: {output_file}", flush=True)
    print("="*70, flush=True)

if __name__ == '__main__':
    main()
