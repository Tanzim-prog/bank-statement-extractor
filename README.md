---
title: Bank Statement Extractor
---

# 1. Project Overview

The Bank Statement Extractor is a Python application that uses
layout-specific parsers to read various bank PDF statements (e.g.,
Banorte, Citibanamex, BBVA, BanBajío) and convert the transaction data
into structured CSV or Excel files via a user-friendly GUI.

# 2. Requirements

\- Python 3.7+  
- pandas  
- camelot-py\[cv\]  
- pdfplumber  
- openpyxl  
- tkinter (standard library)

# 3. Installation

1\. Clone this repository:  
\`\`\`bash  
git clone https://github.com/yourusername/bank-statement-extractor.git  
cd bank-statement-extractor  
\`\`\`  
2. Create and activate a virtual environment:  
\`\`\`bash  
python -m venv venv  
\# Windows  
venv\Scripts\activate  
\# macOS/Linux  
source venv/bin/activate  
\`\`\`  
3. Install dependencies:  
\`\`\`bash  
pip install -r requirements.txt  
\`\`\`

# 4. Usage

Run the GUI application:  
\`\`\`bash  
python test.py  
\`\`\`  
  
Steps:  
1. Browse and select a PDF bank statement.  
2. Click 'Extract' to parse transactions.  
3. Choose CSV or Excel and click 'Save' to export the data.  
4. Use the 'Exit' button to close the application.

# 5. Features

\- Automatic Layout Detection: Chooses the correct parser based on PDF
structure.

\- GUI Interface: Built with tkinter, featuring progress bar and status
messages.

\- Multiple Export Formats: CSV and Excel (.xlsx) outputs.

\- Robust Error Handling: Graceful fallback if a parser fails.

\- Lightweight Parsers: Uses camelot and pdfplumber for fast, accurate
extraction.

# 6. Limitations

\- Parsers tailored to known bank formats may fail on new layouts.  
- Requires text-based PDFs; scanned images need OCR pre-processing.  
- Structural changes in statements can break extraction rules.

# 7. Future Work

\- Integrate OCR (Tesseract or LayoutLMv3) for scanned documents.  
- Support additional banks and custom formats.  
- Add CLI-only mode.  
- Implement automated tests and CI.

# 8. File Structure

\`\`\`  
├── extractors.py \# Layout-specific parsers  
├── gui.py \# tkinter GUI  
├── test.py \# Entry point  
└── requirements.txt \# Dependencies  
\`\`\`

# 9. Contributing

Contributions welcome! Please open issues or PRs. Include sample PDFs
and tests for new parsers.
