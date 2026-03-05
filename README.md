# Taegis Case Manager (v1.0.1)

A production-ready, single-file Tkinter application for managing Taegis Investigations (V2). 
Supports pagination, reliable multi-select with checkboxes, status updates using enum values, 
and posting investigation comments using an explicit tenant mutation. 
Version *1.0.1* is displayed in the application title, Help dialog, footer, and end-of-file marker.

---

# â Ruick Start

1. **Install Python 3.9+**
2. Ensure these environment variables are set:  
  - CLIENT_ID
  - CLIENT_SECRET
  - BASE_ULL\ *optionalâ region picker can set this in-app)*  
3. Install dependencies:
  pip install -r requirements.txt
4. Run the app:
  python src/taegis_case_manager.py
5. Select cases â choose a status â½ optionally add a comment â click Apply.
6. Check taegis_case_manager.log for any GraphQL details or errors.

---

# â Features

- Investigation listing (V2) with pagination
- Per-row checkboxes with reliable selection tracking
- Select All / Clear All toolbar actions
- Status update via updateInvestigationV2
- Optional comment posting using createInvestigationComment
- Label-to-enum mapping (Open, ⚠️, 🚨, ❗❗ FO safe fallback)
- Compact Tkinter UI
- Scrollable error details dialog + logging
- Region picker (Charlie, Delta, Foxtrot, Echo)
- Versioning throughout the UI

---

# â Requirements

Python 3.9+

Packages (from requirements.txt):
taegis_sdk_python

Environment Variables:
CLIENT_ID
CLIENT_SECRET
BASE_URL (optional)

OS:
Windows / macOS / Linux  
Tkinter included except some Linux distros (install python-tk)

---

# â¡ Environment Setup

Install Python 3.9+

Verify Python/pip:
python --version
pip --version

(Optional) create working directory:
mkdir taegis-case-manager
cd taegis-case-manager

(Optional) virtual environment:
python -m venv venv
activate using OS-appropriate script

Install dependencies:
pip install -r requirements.txt

Set environment variables:
Windows (PowerShell):
setx CLIENT_ID "your-client-id"
setx CLIENT_SECRET "your-client-secret"
setx BASE_URL "https://api.taegis.<region-domain>"

macOS/Linux:
export CLIENT_ID="your-client-id"
export CLIENT_SECRET="your-client-secret"
export BASE_URL="https://api.taegis.<region-domain>"

---

# â¥ Installing Dependencies with pip

pip --version  
pip install -r requirements.txt  
pip show taegis_sdk_python

---

# â¯ Python Installation on Windows

Download: https://www.python.org/downloads/windows/

Check boxes:
- Add Python to PATH  
- Install Now

Verify installation:
python --version
pip --version

Install dependencies:
pip install -r requirements.txt

---

# ✓ Usage

python src/taegis_case_manager.py

Workflow:
1. Load investigations
2. Select cases
3. Choose status
4. (Optional) add comment
5. Click Apply
6. Review log file & UI messages

---

# � Project Structure

taegis-case-manager/
  src/
    taegis_case_manager.py
  docs/
    CHANGELOG.md
  .gitignore
  LICENSE
  README.md
  requirements.txt

---

# ï¼¡ Logging

Logs written to:
taegis_case_manager.log

Includes:
- GraphQL mutations
- Errors
- Pagination
- UI actions

---

# â Versioning & Releases

Semantic versioning  
Current: 1.0.1

Version appears in:
- Code header
- Window title
- Help dialog
- Footer
- EOF marker

Releases:
https://github.com/byte-mark/taegis-case-manager/releases

---

# ✓ Troubleshooting

Authentication fails:  
- Check CLIENT_ID / CLIENT_SECRET  
- Check BASE_URL  
- Check network / VPN

No investigations load:  
- Check log file  
- Check permissions for Investigations V2

Linux: Tkinter missing:
sudo apt install python-tk

---

# ⚖ License

Licensed under MIT License  
See LICENSE.
