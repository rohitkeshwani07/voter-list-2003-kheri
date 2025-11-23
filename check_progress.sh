#!/bin/bash

echo "=== Extraction Progress Monitor ==="
echo ""

# Check if process is running
if pgrep -f "extract_names.py" > /dev/null; then
    echo "✓ Extraction process is RUNNING"
else
    echo "✗ Extraction process is NOT running"
fi

echo ""
echo "--- Recent Log Activity ---"
tail -20 extraction.log

echo ""
echo "--- Output File Status ---"
if [ -f "all_names.txt" ]; then
    lines=$(wc -l < all_names.txt)
    size=$(du -h all_names.txt | cut -f1)
    echo "✓ all_names.txt exists"
    echo "  Lines: $lines"
    echo "  Size: $size"
else
    echo "✗ all_names.txt not yet created (will be created after first 10 PDFs)"
fi

echo ""
echo "--- Temp Directory ---"
if [ -d "temp_ocr" ]; then
    count=$(ls temp_ocr/*.png 2>/dev/null | wc -l)
    echo "✓ temp_ocr exists with $count image(s)"
else
    echo "✗ temp_ocr directory not found"
fi
