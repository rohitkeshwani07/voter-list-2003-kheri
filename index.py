import requests
import os
from pathlib import Path

# Create a folder to save PDFs
output_folder = "eci_pdfs"
Path(output_folder).mkdir(exist_ok=True)

# Base URL pattern
base_url = "https://www.eci.gov.in/sir/f3/S24/data/OLDSIRROLL/S24/54/S24_54_{}.pdf"

# Download PDFs from _1 to _281
for i in range(1, 282):
    url = base_url.format(i)
    filename = f"S24_54_{i}.pdf"
    filepath = os.path.join(output_folder, filename)
    
    try:
        print(f"Downloading {filename}... ", end="")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✓ Success")
        else:
            print(f"✗ Failed (Status: {response.status_code})")
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")

print(f"\nDownload complete! Files saved in '{output_folder}' folder")
