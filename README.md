
# Taegis Case Manager (v1.0.1)

A production-ready, single-file Python/Tkinter application for managing Taegis Investigations (V2). 
This tool allows for the status of multiple cases to updated at once with the option to add a comment upon update.

Supports pagination, reliable multi-select with checkboxes, status updates using enum values, 
and posting case comments.

![Taegis Case Manager Screenshot](https://github.com/byte-mark/taegis-case-manager/blob/main/assets/taegis_case_manager_image_v1_0_1.png?raw=true)


---

# Quick Start

1. **Install Python 3.9+**
2. Ensure these environment variables are set:  
- `CLIENT_ID`
- `CLIENT_SECRET`
- `BASE_URL` (select from region picker)
3. Install dependencies:
  pip install -r requirements.txt
4. Run the app:
  python src/taegis_case_manager.py
5. Select cases and choose a status
  optionally add a comment
  click Apply.
6. Check taegis_case_manager.log for any GraphQL details or errors.

---

# Features

- Investigation listing with pagination
- Per-row checkboxes with reliable selection tracking
- Select All / Clear All toolbar actions
- Optional comment posting using createInvestigationComment
- Quick multi-field filtering of results
- Compact Tkinter UI
- Scrollable error details dialog + logging
- Region picker (Charlie, Delta, Foxtrot, Echo)

---

# Requirements

Python 3.9+

Packages (from requirements.txt):
taegis_sdk_python

Environment Variables:
CLIENT_ID
CLIENT_SECRET
BASE_URL (Select from list)

OS:
Windows / macOS / Linux  
Tkinter included except some Linux distros (install python-tk)

---

# Environment Setup

Install Python 3.9+ (available on the Microsoft App Store for Windows user)

Via CLI: (Windows/Linux/Mac)

Verify Python/pip:
python --version
pip --version

Install dependencies:
pip install -r requirements.txt

---

# Usage

python src/taegis_case_manager.py

Provide your API Client ID and Client Secret found in Taegis under "Tenant Settings" > Manage API Credentials

Note: The "API Credential Name" you choose will be the "user" that will show in comment updates.

Workflow:
1. Load investigations
2. Select cases
3. Choose status
4. (Optional) add comment
5. Click Apply
6. Review log file & UI messages

---

# Project Structure

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

# Logging

Logs written to:
taegis_case_manager.log

Includes:
- GraphQL mutations
- Errors
- Pagination
- UI actions

---

# Versioning & Releases

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

# Troubleshooting

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

# License

Licensed under MIT License  
See LICENSE.
