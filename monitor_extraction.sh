#!/bin/bash

echo "=== PDF Name Extraction Monitor ==="
echo ""

# Check if process is running
if pgrep -f "extract_all_pdfs.py" > /dev/null; then
    echo "✓ Extraction is RUNNING"
else
    echo "✗ Extraction is NOT running (may have completed or stopped)"
fi

echo ""
echo "--- Recent Activity ---"
tail -15 extraction_final.log

echo ""
echo "--- Output File Status ---"
if [ -f "all_names_final.csv" ]; then
    lines=$(wc -l < all_names_final.csv)
    size=$(du -h all_names_final.csv | cut -f1)
    # Subtract 1 for header row
    names=$((lines - 1))
    echo "✓ all_names_final.csv exists"
    echo "  Total lines: $lines"
    echo "  Names extracted: $names"
    echo "  File size: $size"
else
    echo "✗ all_names_final.csv not yet created"
fi

echo ""
